#!/bin/bash

# Script to query KV cache for document processing
# For use with LlamaCagUI

set -e  # Exit immediately if a command exits with a non-zero status

# Check if we have the required arguments
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <model_path> <cache_path> <query>"
    exit 1
fi

# Get arguments
MODEL_PATH="$1"
CACHE_PATH="$2"
QUERY="$3"

# Define directories
BASE_DIR="$HOME/.llamacag"
LOGS_DIR="$BASE_DIR/logs"

# Create directories if they don't exist
mkdir -p "$LOGS_DIR"

# Generate a timestamp for the log file
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
LOG_FILE="$LOGS_DIR/query_kv_cache_${TIMESTAMP}.log"

# Log the start of the process
echo "$(date): Starting KV cache query" | tee -a "$LOG_FILE"
echo "$(date): Using model: $MODEL_PATH" | tee -a "$LOG_FILE"
echo "$(date): Cache path: $CACHE_PATH" | tee -a "$LOG_FILE"
echo "$(date): Query: $QUERY" | tee -a "$LOG_FILE"

# Create a simple Python script to process the query
TEMP_SCRIPT=$(mktemp)
cat > "$TEMP_SCRIPT" << 'EOF'
import sys
import os
import json
import time
from pathlib import Path

# Get command line arguments
model_path = sys.argv[1]
cache_path = sys.argv[2]
query = sys.argv[3]
base_dir = sys.argv[4]

# Check if the cache exists
if not os.path.exists(cache_path):
    print(f"Error: Cache file not found: {cache_path}")
    sys.exit(1)

# Load the cache
with open(cache_path, 'r', encoding='utf-8') as f:
    try:
        cache_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Invalid cache file format: {cache_path}")
        sys.exit(1)

# In a real implementation, this would use the model and cache to generate a response
# For now, we'll just echo back the query and some info from the cache

# Simulate some processing time
time.sleep(1)

# Prepare the response
response = {
    "query": query,
    "cache_info": {
        "name": cache_data.get("cache_name", "Unknown"),
        "model": os.path.basename(cache_data.get("model_path", "Unknown")),
        "document_sample": cache_data.get("first_100_chars", "No sample available")
    },
    "response": f"This is a response to: {query}\n\nContext from document: {cache_data.get('first_100_chars', 'No context available')}"
}

# Update the usage registry
registry_path = os.path.join(base_dir, "usage_registry.json")
if os.path.exists(registry_path):
    with open(registry_path, 'r', encoding='utf-8') as f:
        try:
            registry = json.load(f)
        except json.JSONDecodeError:
            registry = {"queries": []}
else:
    registry = {"queries": []}

# Add the new query to the registry
registry["queries"].append({
    "timestamp": time.time(),
    "query": query,
    "cache": os.path.basename(cache_path),
    "model": os.path.basename(model_path)
})

# Save the updated registry
with open(registry_path, 'w', encoding='utf-8') as f:
    json.dump(registry, f, indent=2)

# Output the response
print(json.dumps(response, indent=2))

print(f"Query processed successfully")
print(f"Usage registry updated: {registry_path}")
EOF

# Run the Python script
python3 "$TEMP_SCRIPT" "$MODEL_PATH" "$CACHE_PATH" "$QUERY" "$BASE_DIR" 2>&1 | tee -a "$LOG_FILE"

# Clean up
rm "$TEMP_SCRIPT"

# Log the completion
echo "$(date): KV cache query completed" | tee -a "$LOG_FILE"

# Exit with success
exit 0