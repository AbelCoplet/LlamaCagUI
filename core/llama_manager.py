#!/usr/bin/env python3
"""
llama.cpp management for LlamaCag UI
Handles installation, updates, and version checking for llama.cpp.
"""
import os
import sys
import subprocess
import logging
from pathlib import Path
import shutil
import time
from typing import Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal


class LlamaManager(QObject):
    """Manages llama.cpp installation and updates"""

    # Signals
    installation_progress = pyqtSignal(int, str)  # progress percentage, message
    installation_complete = pyqtSignal(bool, str)  # success, message

    def __init__(self, config):
        """Initialize llama manager"""
        super().__init__()
        self.config = config
        self.llamacpp_path = Path(os.path.expanduser(config.get('LLAMACPP_PATH', '~/Documents/llama.cpp')))

    def is_installed(self) -> bool:
        """Check if llama.cpp is installed"""
        # Check if directory exists
        if not self.llamacpp_path.exists():
            return False
        # Check if main executable exists
        main_executable = self.llamacpp_path / 'build' / 'bin' / 'main'
        if not main_executable.exists():
            return False
        return True

    def get_version(self) -> str:
        """Get the installed version of llama.cpp"""
        if not self.is_installed():
            return "Not installed"
        try:
            # Try to get version from git
            result = subprocess.run(
                f"cd {self.llamacpp_path} && git describe --tags",
                shell=True, check=True, capture_output=True, text=True
            )
            return result.stdout.strip()
        except Exception:
            # Fall back to "unknown"
            return "Unknown"

    def is_update_available(self) -> bool:
        """Check if an update is available for llama.cpp"""
        if not self.is_installed():
            return False
        try:
            # Fetch latest updates
            subprocess.run(
                f"cd {self.llamacpp_path} && git fetch",
                shell=True, check=True, capture_output=True
            )
            # Check if local is behind remote
            result = subprocess.run(
                f"cd {self.llamacpp_path} && git status -uno",
                shell=True, check=True, capture_output=True, text=True
            )
            return "Your branch is behind" in result.stdout
        except Exception as e:
            logging.error(f"Error checking for updates: {str(e)}")
            return False

    def install(self) -> bool:
        """Install llama.cpp"""
        # Start installation in a separate thread
        import threading
        threading.Thread(
            target=self._install_thread,
            daemon=True
        ).start()
        return True

    def _install_thread(self):
        """Thread function for llama.cpp installation"""
        try:
            # Create directory if it doesn't exist
            self.llamacpp_path = Path(os.path.expanduser(self.llamacpp_path))
            if not self.llamacpp_path.exists():
                os.makedirs(self.llamacpp_path, parents=True)

            # Signal progress
            self.installation_progress.emit(5, "Creating directories...")

            # Clone repository
            if not (self.llamacpp_path / '.git').exists():
                self.installation_progress.emit(10, "Cloning llama.cpp repository...")

                # Use a more reliable git clone command
                cmd = f"git clone https://github.com/ggerganov/llama.cpp.git {self.llamacpp_path}"
                process = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)

                if process.returncode != 0:
                    raise Exception(f"Git clone failed: {process.stderr}")
            else:
                self.installation_progress.emit(10, "Updating existing repository...")

                # Use a more reliable git pull command
                cmd = f"cd {self.llamacpp_path} && git pull"
                process = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)

                if process.returncode != 0:
                    raise Exception(f"Git pull failed: {process.stderr}")

            # Create build directory
            build_path = self.llamacpp_path / 'build'
            if not build_path.exists():
                build_path.mkdir(parents=True)

            # Signal progress
            self.installation_progress.emit(30, "Configuring build...")

            # Configure build with better error handling
            cmd = f"cd {build_path} && cmake .."
            process = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)

            if process.returncode != 0:
                raise Exception(f"CMake configuration failed: {process.stderr}")

            # Signal progress
            self.installation_progress.emit(50, "Building llama.cpp (this may take a while)...")

            # Build with better error handling
            cmd = f"cd {build_path} && make -j{os.cpu_count() or 4}"
            process = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)

            if process.returncode != 0:
                raise Exception(f"Build failed: {process.stderr}")

            # Create models directory
            models_path = self.llamacpp_path / 'models'
            if not models_path.exists():
                models_path.mkdir(parents=True)

            # Signal completion
            self.installation_progress.emit(100, "Installation complete!")
            self.installation_complete.emit(True, "llama.cpp installed successfully!")

        except Exception as e:
            logging.error(f"Installation failed: {str(e)}")
            self.installation_complete.emit(False, f"Installation failed: {str(e)}")

    def update_config(self, config):
        """Update configuration"""
        self.config = config
        self.llamacpp_path = Path(os.path.expanduser(config.get('LLAMACPP_PATH', '~/Documents/llama.cpp')))