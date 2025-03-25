#!/bin/bash

# Script to create KV cache for document processing
# For use with LlamaCagUI

set -e  # Exit immediately if a command exits with a non-zero status

# Check if we have the required arguments
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <model_path> <document_path> [cache_name]"
    exit 1
fi

# Get arguments
MODEL_PATH="$1"
DOCUMENT_PATH="$2"
CACHE_NAME="${3:-$(basename "$DOCUMENT_PATH")}"

# Define directories
BASE_DIR="$HOME/.llamacag"
CACHE_DIR="$BASE_DIR/cache"
LOGS_DIR="$BASE_DIR/logs"

# Create directories if they don't exist
mkdir -p "$CACHE_DIR"
mkdir -p "$LOGS_DIR"

# Generate a timestamp for the log file
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
LOG_FILE="$LOGS_DIR/create_kv_cache_${TIMESTAMP}.log"

# Log the start of the process
echo "$(date): Starting KV cache creation for document: $DOCUMENT_PATH" | tee -a "$LOG_FILE"
echo "$(date): Using model: $MODEL_PATH" | tee -a "$LOG_FILE"
echo "$(date): Cache will be saved as: $CACHE_NAME" | tee -a "$LOG_FILE"

# Create a simple Python script to process the document
TEMP_SCRIPT=$(mktemp)
cat > "$TEMP_SCRIPT" << 'EOF'
import sys
import os
import json
from pathlib import Path
import hashlib

# Get command line arguments
model_path = sys.argv[1]
document_path = sys.argv[2]
cache_name = sys.argv[3]
cache_dir = sys.argv[4]
base_dir = sys.argv[5]

# Create a hash for the model and document combination
def create_hash(model_path, document_path):
    combined = f"{model_path}|{document_path}"
    return hashlib.md5(combined.encode()).hexdigest()

# Generate cache path
cache_hash = create_hash(model_path, document_path)
cache_path = os.path.join(cache_dir, f"{cache_name}_{cache_hash}.json")

# Read the document
with open(document_path, 'r', encoding='utf-8') as f:
    document_text = f.read()

# Create a simple representation of the processed document
# In a real implementation, this would use the model to create embeddings
cache_data = {
    "model_path": model_path,
    "document_path": document_path,
    "cache_name": cache_name,
    "hash": cache_hash,
    "text_length": len(document_text),
    "first_100_chars": document_text[:100]
}

# Save the cache
with open(cache_path, 'w', encoding='utf-8') as f:
    json.dump(cache_data, f, indent=2)

# Update the registry
registry_path = os.path.join(base_dir, "cache_registry.json")
if os.path.exists(registry_path):
    with open(registry_path, 'r', encoding='utf-8') as f:
        try:
            registry = json.load(f)
        except json.JSONDecodeError:
            registry = {"caches": []}
else:
    registry = {"caches": []}

# Add the new cache to the registry
registry["caches"].append({
    "name": cache_name,
    "model": os.path.basename(model_path),
    "document": os.path.basename(document_path),
    "path": cache_path,
    "created": Path(cache_path).stat().st_mtime
})

# Save the updated registry
with open(registry_path, 'w', encoding='utf-8') as f:
    json.dump(registry, f, indent=2)

print(f"KV cache created successfully: {cache_path}")
print(f"Registry updated: {registry_path}")
EOF

# Run the Python script
python3 "$TEMP_SCRIPT" "$MODEL_PATH" "$DOCUMENT_PATH" "$CACHE_NAME" "$CACHE_DIR" "$BASE_DIR" 2>&1 | tee -a "$LOG_FILE"

# Clean up
rm "$TEMP_SCRIPT"

# Log the completion
echo "$(date): KV cache creation completed" | tee -a "$LOG_FILE"

# Exit with success
exit 0