#!/bin/bash
# Set up environment
export PYTHONPATH="$PYTHONPATH:$(pwd)"
# Ensure logs directory exists
mkdir -p ~/.llamacag/logs
# Run the application
python3 main.py "$@"