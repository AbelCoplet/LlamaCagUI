#!/usr/bin/env python3
"""
Utility for running external scripts with progress tracking
"""

import os
import subprocess
import time
import logging
import threading
from typing import List, Callable, Optional, Any

def run_script(
    command: List[str],
    progress_callback: Optional[Callable[[int], Any]] = None,
    timeout: int = 300
) -> subprocess.CompletedProcess:
    """
    Run an external script and track its progress
    
    Args:
        command: List of command and arguments to run
        progress_callback: Function to call with progress percentage (0-100)
        timeout: Maximum time to wait for script completion (seconds)
        
    Returns:
        CompletedProcess instance with returncode, stdout, and stderr
    """
    try:
        # Check if script exists
        if not os.path.exists(command[0]):
            logging.error(f"Script not found: {command[0]}")
            raise FileNotFoundError(f"Script not found: {command[0]}")
            
        # Check if script is executable
        if not os.access(command[0], os.X_OK):
            logging.warning(f"Script is not executable: {command[0]}")
            try:
                os.chmod(command[0], 0o755)
                logging.info(f"Set executable permission on {command[0]}")
            except Exception as e:
                logging.error(f"Failed to set executable permission: {e}")
                raise PermissionError(f"Cannot execute script: {command[0]}")
        
        # Start the process
        logging.info(f"Running script: {' '.join(command)}")
        
        # Create a process
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )
        
        # Update progress
        if progress_callback:
            progress_callback(0)
        
        # Track progress in a separate thread
        def progress_tracker():
            start_time = time.time()
            while process.poll() is None:
                elapsed_time = time.time() - start_time
                if timeout > 0:
                    # Calculate progress based on elapsed time
                    progress = min(int((elapsed_time / timeout) * 100), 99)
                    if progress_callback:
                        progress_callback(progress)
                        
                time.sleep(0.5)
        
        # Start progress tracker thread
        progress_thread = threading.Thread(target=progress_tracker, daemon=True)
        progress_thread.start()
        
        # Wait for process to complete
        stdout, stderr = process.communicate(timeout=timeout)
        
        # Make sure progress thread is stopped
        if progress_thread.is_alive():
            progress_thread.join(1)
            
        # Update final progress
        if progress_callback:
            progress_callback(100)
            
        # Create CompletedProcess for compatibility
        result = subprocess.CompletedProcess(
            args=command,
            returncode=process.returncode,
            stdout=stdout,
            stderr=stderr
        )
        
        return result
        
    except subprocess.TimeoutExpired:
        logging.error(f"Script execution timed out after {timeout} seconds")
        if 'process' in locals():
            process.kill()
            stdout, stderr = process.communicate()
            return subprocess.CompletedProcess(
                args=command,
                returncode=-1,
                stdout=stdout,
                stderr=f"Script execution timed out after {timeout} seconds\n{stderr}"
            )
        else:
            return subprocess.CompletedProcess(
                args=command,
                returncode=-1,
                stdout="",
                stderr=f"Script execution timed out after {timeout} seconds"
            )
    except Exception as e:
        logging.error(f"Error running script: {e}")
        return subprocess.CompletedProcess(
            args=command,
            returncode=-1,
            stdout="",
            stderr=f"Error running script: {str(e)}"
        )