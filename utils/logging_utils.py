#!/usr/bin/env python3
"""
Logging utilities for LlamaCag UI
Provides logging configuration and utilities.
"""
import os
import sys
import logging
from pathlib import Path
import datetime
def setup_logging(log_dir: str = None, level: int = logging.INFO):
    """
    Set up logging for the application
    Args:
        log_dir: Directory to store log files (default: ~/.llamacag/logs)
        level: Logging level (default: INFO)
    """
    # Set up log directory
    if log_dir is None:
        log_dir = os.path.expanduser('~/.llamacag/logs')
    os.makedirs(log_dir, exist_ok=True)
    # Log file path with timestamp
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'llamacag_{timestamp}.log')
    # Configure logging
    handlers = [
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    # Log the startup
    logging.info(f"Logging initialized. Log file: {log_file}")
    return log_file