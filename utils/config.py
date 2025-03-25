#!/usr/bin/env python3
"""
Configuration management for LlamaCag UI.
Manages application configuration, including loading from .env file.
"""
import os
import sys
import logging
from pathlib import Path
import json
from typing import Dict, Optional, Any
import dotenv
class ConfigManager:
    """Manages application configuration"""
    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration manager"""
        # Default paths
        self.env_file = env_file or os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        self.user_config_dir = os.path.expanduser('~/.llamacag')
        self.user_config_file = os.path.join(self.user_config_dir, 'config.json')
        # Create user config directory if it doesn't exist
        os.makedirs(self.user_config_dir, exist_ok=True)
        # Load the .env file
        self.env_vars = self._load_env_file()
        # Load user config
        self.user_config = self._load_user_config()
        # Merged config
        self.config = {**self.env_vars, **self.user_config}
    def _load_env_file(self) -> Dict[str, Any]:
        """Load environment variables from .env file"""
        # Check if .env file exists
        if not os.path.exists(self.env_file):
            # Try to find .env in the parent directory
            parent_env = os.path.join(os.path.dirname(os.path.dirname(self.env_file)), '.env')
            if os.path.exists(parent_env):
                self.env_file = parent_env
            else:
                # Try to create from example
                example_env = os.path.join(os.path.dirname(self.env_file), '.env.example')
                if os.path.exists(example_env):
                    with open(example_env, 'r') as src, open(self.env_file, 'w') as dst:
                        dst.write(src.read())
                        logging.info(f"Created .env file from example at {self.env_file}")
                else:
                    # Create empty .env file
                    with open(self.env_file, 'w') as f:
                        f.write("# LlamaCag UI Configuration\n")
                        logging.info(f"Created empty .env file at {self.env_file}")
        # Load .env file
        dotenv.load_dotenv(self.env_file)
        # Get all environment variables
        env_vars = {}
        with open(self.env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value.strip('"\'')
        return env_vars
    def _load_user_config(self) -> Dict[str, Any]:
        """Load user configuration from file"""
        # Check if user config file exists
        if not os.path.exists(self.user_config_file):
            # Create empty config
            with open(self.user_config_file, 'w') as f:
                json.dump({}, f, indent=2)
            return {}
        # Load user config
        try:
            with open(self.user_config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load user config: {str(e)}")
            return {}
    def save_config(self):
        """Save configuration to files"""
        # Save user config
        try:
            # Only save user config keys, not env vars
            # Extract user config keys from merged config
            user_keys = set(self.user_config.keys())
            save_config = {k: self.config[k] for k in user_keys if k in self.config}
            # Add any new keys that aren't in env_vars
            env_keys = set(self.env_vars.keys())
            new_keys = set(self.config.keys()) - env_keys - user_keys
            for key in new_keys:
                save_config[key] = self.config[key]
            with open(self.user_config_file, 'w') as f:
                json.dump(save_config, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save user config: {str(e)}")
    def get_config(self) -> Dict[str, Any]:
        """Get the merged configuration"""
        return self.config
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        return self.config.get(key, default)
    def set(self, key: str, value: Any):
        """Set a configuration value"""
        self.config[key] = value
        # If it's an environment variable, update .env file
        if key in self.env_vars:
            self.env_vars[key] = value
            self._save_env_file()
        else:
            # Otherwise, update user config
            self.user_config[key] = value
            self.save_config()
    def _save_env_file(self):
        """Save environment variables to .env file"""
        try:
            # Read current .env file to preserve comments and formatting
            with open(self.env_file, 'r') as f:
                lines = f.readlines()
            # Update values
            new_lines = []
            for line in lines:
                line = line.rstrip()
                if line and not line.startswith('#') and '=' in line:
                    key = line.split('=', 1)[0].strip()
                    if key in self.env_vars:
                        value = self.env_vars[key]
                        line = f"{key}={value}"
                new_lines.append(line)
            # Write back
            with open(self.env_file, 'w') as f:
                f.write('\n'.join(new_lines) + '\n')
        except Exception as e:
            logging.error(f"Failed to save .env file: {str(e)}")