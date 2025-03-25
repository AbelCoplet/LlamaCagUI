#!/bin/bash

# Fixed document processor for LlamaCagUI that focuses on reliability
# This script prepares documents for context augmentation

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

# Define log file
LOG_DIR="$HOME/.llamacag/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/create_cache_$(date +%Y%m%d_%H%M%S).log"

# Log start of the process
echo "Starting document processing at $(date)" > "$LOG_FILE"
echo "Model: $MODEL_PATH" >> "$LOG_FILE"
echo "Document: $DOCUMENT_PATH" >> "$LOG_FILE"
echo "Cache path: $CACHE_PATH" >> "$LOG_FILE"
echo "Context size: $CONTEXT_SIZE tokens" >> "$LOG_FILE"

# Create cache directory
mkdir -p "$(dirname "$CACHE_PATH")"

# Process document
if [ -f "$DOCUMENT_PATH" ]; then
    # Get file info
    FILE_SIZE=$(wc -c < "$DOCUMENT_PATH")
    FILE_EXT="${DOCUMENT_PATH##*.}"
    
    echo "File size: $FILE_SIZE bytes" >> "$LOG_FILE"
    echo "File type: $FILE_EXT" >> "$LOG_FILE"
    
    # Simple token estimation (rough approximation)
    TOKEN_ESTIMATE=$(($FILE_SIZE / 4))
    echo "Estimated tokens: $TOKEN_ESTIMATE" >> "$LOG_FILE"
    
    # For large documents, create a trimmed version
    if [ "$TOKEN_ESTIMATE" -gt "$CONTEXT_SIZE" ]; then
        echo "Document may exceed context window, trimming" >> "$LOG_FILE"
        
        # Calculate approximate byte limit
        BYTE_LIMIT=$(($CONTEXT_SIZE * 4))
        
        # Create truncated version
        echo "Truncating to approximately $BYTE_LIMIT bytes" >> "$LOG_FILE"
        head -c "$BYTE_LIMIT" "$DOCUMENT_PATH" > "$CACHE_PATH"
    else
        # Document fits in context window, copy it directly
        echo "Document should fit in context window" >> "$LOG_FILE"
        cp "$DOCUMENT_PATH" "$CACHE_PATH"
    fi
    
    # Create metadata file
    cat > "$CACHE_PATH.json" << EOF
{
    "model_path": "$MODEL_PATH",
    "document_path": "$DOCUMENT_PATH",
    "document_size": $FILE_SIZE,
    "token_estimate": $TOKEN_ESTIMATE,
    "context_size": $CONTEXT_SIZE,
    "timestamp": "$(date)"
}
EOF
    
    # Create master cache
    MASTER_CACHE="$HOME/cag_project/kv_caches/master_cache.bin"
    mkdir -p "$(dirname "$MASTER_CACHE")"
    cp "$CACHE_PATH" "$MASTER_CACHE"
    cp "$CACHE_PATH.json" "$MASTER_CACHE.json"
    
    echo "Created master cache at $MASTER_CACHE" >> "$LOG_FILE"
    echo "Processing complete at $(date)" >> "$LOG_FILE"
    
    # Print success message
    echo "Document successfully processed"
    echo "Estimated tokens: $TOKEN_ESTIMATE"
    
    exit 0
else
    echo "ERROR: Document not found: $DOCUMENT_PATH" | tee -a "$LOG_FILE"
    exit 1
fi