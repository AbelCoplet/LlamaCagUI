#!/usr/bin/env python3
"""
Script runner utility for LlamaCag UI
Provides functionality for running bash scripts with progress reporting.
"""
import os
import sys
import subprocess
import logging
import threading
import time
import re
from typing import Optional, Callable, List, Tuple
class ScriptProcess:
    """Represents a running script process with its output and status"""
    def __init__(self, command: List[str], returncode: int = 0, stdout: str = "", stderr: str = ""):
        """Initialize script process"""
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        # Calculate command string
        if isinstance(command, list):
            self.command_str = ' '.join(command)
        else:
            self.command_str = str(command)
def run_script(command, progress_callback: Optional[Callable[[int], None]] = None,
              timeout: int = 3600) -> ScriptProcess:
    """
    Run a shell script or command with progress reporting
    Args:
        command: Command to run (list or string)
        progress_callback: Callback function for progress updates (0-100)
        timeout: Timeout in seconds
    Returns:
        ScriptProcess object with command, returncode, stdout, stderr
    """
    # Convert command to string if it's a list
    if isinstance(command, list):
        cmd_str = ' '.join(command)
    else:
        cmd_str = str(command)
        command = cmd_str.split()  # For the ScriptProcess object
    # Create process
    process = subprocess.Popen(
        cmd_str,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1  # Line buffered
    )
    # Output buffers
    stdout_lines = []
    stderr_lines = []
    # Progress pattern
    progress_pattern = re.compile(r'PROGRESS:(\d+)')
    # Last progress value
    last_progress = 0
    # Function to handle process output
    def handle_output():
        nonlocal last_progress
        # Read stdout
        for line in process.stdout:
            stdout_lines.append(line)
            # Check for progress indicator
            if progress_callback:
                progress_match = progress_pattern.search(line)
                if progress_match:
                    try:
                        progress = int(progress_match.group(1))
                        if progress != last_progress:
                            progress_callback(progress)
                            last_progress = progress
                    except:
                        pass
        # Read stderr
        for line in process.stderr:
            stderr_lines.append(line)
    # Start