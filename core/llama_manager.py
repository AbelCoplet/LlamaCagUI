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
from typing import Optional, Tuple, List
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox


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
        logging.info(f"Initialized LlamaManager with path: {self.llamacpp_path}")

    def is_installed(self) -> bool:
        """Check if llama.cpp is installed with improved detection"""
        # Check if directory exists
        if not self.llamacpp_path.exists():
            logging.warning(f"llama.cpp directory not found at {self.llamacpp_path}")
            return False
            
        # Check for various possible executable locations
        possible_executables = [
            self.llamacpp_path / 'build' / 'bin' / 'main',  # Standard location
            self.llamacpp_path / 'build' / 'main',          # Alternate location
            self.llamacpp_path / 'main'                     # Simple build location
        ]
        
        # Check for macOS specific locations
        if sys.platform == 'darwin':
            possible_executables.extend([
                self.llamacpp_path / 'build' / 'bin' / 'llama-cli',
                self.llamacpp_path / 'build' / 'llama-cli'
            ])
        
        # Check if any CMake files exist (indication of successful build)
        cmake_files = [
            self.llamacpp_path / 'build' / 'CMakeCache.txt',
            self.llamacpp_path / 'build' / 'cmake_install.cmake'
        ]
        
        # Look for either executables or cmake files as evidence of installation
        for exe in possible_executables:
            if exe.exists():
                logging.info(f"Found llama.cpp executable at {exe}")
                return True
                
        for cmake_file in cmake_files:
            if cmake_file.exists():
                logging.info(f"Found llama.cpp build file at {cmake_file}")
                return True
        
        # As a last resort, check if the source code exists and has been built at all
        if (self.llamacpp_path / 'CMakeLists.txt').exists() and (self.llamacpp_path / 'build').exists():
            logging.info("Found llama.cpp source and build directory")
            return True
            
        logging.warning("No evidence of llama.cpp installation found")
        return False

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

    def _check_dependencies(self) -> List[str]:
        """Check if required dependencies are installed"""
        dependencies = {
            'git': 'git --version',
            'cmake': 'cmake --version',
            'make': 'make --version'
        }
        
        missing = []
        for dep, cmd in dependencies.items():
            try:
                result = subprocess.run(cmd, shell=True, check=False, capture_output=True, text=True)
                if result.returncode != 0:
                    missing.append(dep)
            except Exception:
                missing.append(dep)
                
        return missing

    def _install_homebrew(self) -> bool:
        """Install Homebrew if not already installed"""
        try:
            # Check if brew is already installed
            result = subprocess.run(
                "which brew", 
                shell=True, 
                check=False, 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                return True  # Already installed
                
            # Install Homebrew
            self.installation_progress.emit(10, "Installing Homebrew (this may take a while)...")
            
            homebrew_install_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
            result = subprocess.run(
                homebrew_install_cmd,
                shell=True,
                check=False,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logging.error(f"Failed to install Homebrew: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Error installing Homebrew: {str(e)}")
            return False

    def _install_dependencies(self, missing_deps: List[str]) -> bool:
        """Install missing dependencies using Homebrew"""
        try:
            # First make sure Homebrew is installed
            if not self._install_homebrew():
                return False
                
            # Install each missing dependency
            for dep in missing_deps:
                self.installation_progress.emit(15, f"Installing {dep} (this may take a while)...")
                
                cmd = f"brew install {dep}"
                result = subprocess.run(
                    cmd,
                    shell=True,
                    check=False,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    logging.error(f"Failed to install {dep}: {result.stderr}")
                    return False
                    
            return True
            
        except Exception as e:
            logging.error(f"Error installing dependencies: {str(e)}")
            return False

    def install(self) -> bool:
        """Install llama.cpp"""
        # Check dependencies first
        missing_deps = self._check_dependencies()
        if missing_deps:
            self.installation_progress.emit(5, f"Checking dependencies... Missing: {', '.join(missing_deps)}")
            
            # Try to install missing dependencies
            if not self._install_dependencies(missing_deps):
                error_msg = f"Failed to install required dependencies: {', '.join(missing_deps)}.\n\nPlease install them manually with:\nbrew install {' '.join(missing_deps)}"
                self.installation_complete.emit(False, error_msg)
                return False
                
            # Re-check dependencies after install attempt
            missing_deps = self._check_dependencies()
            if missing_deps:
                error_msg = f"Still missing dependencies after installation attempt: {', '.join(missing_deps)}.\n\nPlease install them manually with:\nbrew install {' '.join(missing_deps)}"
                self.installation_complete.emit(False, error_msg)
                return False
        
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
            self.installation_progress.emit(20, "Creating directories...")

            # Clone repository
            if not (self.llamacpp_path / '.git').exists():
                self.installation_progress.emit(30, "Cloning llama.cpp repository...")

                # Use a more reliable git clone command
                cmd = f"git clone https://github.com/ggerganov/llama.cpp.git {self.llamacpp_path}"
                process = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)

                if process.returncode != 0:
                    raise Exception(f"Git clone failed: {process.stderr}")
            else:
                self.installation_progress.emit(30, "Updating existing repository...")

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
            self.installation_progress.emit(50, "Configuring build...")

            # Configure build with better error handling
            cmd = f"cd {self.llamacpp_path} && cmake -B build"
            process = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)

            if process.returncode != 0:
                raise Exception(f"CMake configuration failed: {process.stderr}")

            # Signal progress
            self.installation_progress.emit(70, "Building llama.cpp (this may take a while)...")

            # Build with better error handling
            cpu_count = os.cpu_count() or 4
            cmd = f"cd {self.llamacpp_path} && cmake --build build -j {cpu_count}"
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