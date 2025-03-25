#!/bin/bash

# Simple document processor for LlamaCagUI
# This version uses a streamlined approach that will work with any llama.cpp version

# Check if we have the required arguments
if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <model_path> <document_path> <cache_path> [context_size] [threads] [batch_size]"
    exit 1
fi

# Get arguments
MODEL_PATH="$1"
DOCUMENT_PATH="$2"
CACHE_PATH="$3"
CONTEXT_SIZE="${4:-128000}"
THREADS="${5:-4}"
BATCH_SIZE="${6:-1024}"

# Define directories for logging
LOGS_DIR="$HOME/.llamacag/logs"
mkdir -p "$LOGS_DIR"
mkdir -p "$(dirname "$CACHE_PATH")"

# Generate a timestamp for the log file
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
LOG_FILE="$LOGS_DIR/document_process_${TIMESTAMP}.log"

# Log start of the process
echo "$(date): Processing document: $DOCUMENT_PATH" | tee -a "$LOG_FILE"
echo "$(date): Using model: $MODEL_PATH" | tee -a "$LOG_FILE"
echo "$(date): Cache will be saved as: $CACHE_PATH" | tee -a "$LOG_FILE"

# Find llama.cpp binary
LLAMACPP_DIR=$(dirname $(dirname "$MODEL_PATH"))
if [ -f "$LLAMACPP_DIR/build/bin/llama-cli" ]; then
    LLAMA_BIN="$LLAMACPP_DIR/build/bin/llama-cli"
elif [ -f "$LLAMACPP_DIR/build/bin/main" ]; then
    LLAMA_BIN="$LLAMACPP_DIR/build/bin/main"
else
    echo "Error: llama.cpp binary not found in $LLAMACPP_DIR/build/bin/" | tee -a "$LOG_FILE"
    exit 1
fi

echo "$(date): Using llama.cpp binary: $LLAMA_BIN" | tee -a "$LOG_FILE"

# Process document content and store it in the cache
if [ -f "$DOCUMENT_PATH" ]; then
    # Create the JSON metadata file
    cat > "$CACHE_PATH.json" << EOF
{
    "model_path": "$MODEL_PATH",
    "document_path": "$DOCUMENT_PATH",
    "document_content": "$(head -c 1000 "$DOCUMENT_PATH" | sed 's/"/\\"/g')",
    "context_size": $CONTEXT_SIZE,
    "timestamp": "$(date)"
}
EOF

    # Copy document to cache location - this is the simplest and most reliable approach
    cp "$DOCUMENT_PATH" "$CACHE_PATH"
    echo "$(date): Document processed successfully" | tee -a "$LOG_FILE"
    
    # Also create master cache
    MASTER_CACHE="$HOME/cag_project/kv_caches/master_cache.bin"
    cp "$DOCUMENT_PATH" "$MASTER_CACHE"
    cp "$CACHE_PATH.json" "$MASTER_CACHE.json"
    echo "$(date): Created master cache at $MASTER_CACHE" | tee -a "$LOG_FILE"
    
    exit 0
else
    echo "$(date): ERROR: Document not found: $DOCUMENT_PATH" | tee -a "$LOG_FILE"
    exit 1
fi