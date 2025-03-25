#!/bin/bash

# Fixed document query script that ensures output is properly displayed
# For use with LlamaCagUI

# Check if we have the required arguments
if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <model_path> <cache_path> <query> [max_tokens] [options]"
    exit 1
fi

# Get arguments
MODEL_PATH="$1"
CACHE_PATH="$2"
QUERY="$3"
MAX_TOKENS="${4:-1024}"

# Extract query from file if needed
if [[ "$QUERY" == @* ]]; then
    QUERY_FILE="${QUERY:1}"
    if [ -f "$QUERY_FILE" ]; then
        QUERY_CONTENT=$(cat "$QUERY_FILE")
    else
        echo "Error: Query file not found: $QUERY_FILE"
        exit 1
    fi
else
    QUERY_CONTENT="$QUERY"
fi

# Find llama.cpp binary
LLAMACPP_DIR=$(dirname $(dirname "$MODEL_PATH"))
if [ -f "$LLAMACPP_DIR/build/bin/llama-cli" ]; then
    LLAMA_BIN="$LLAMACPP_DIR/build/bin/llama-cli"
elif [ -f "$LLAMACPP_DIR/build/bin/main" ]; then
    LLAMA_BIN="$LLAMACPP_DIR/build/bin/main"
else
    echo "Error: llama.cpp binary not found"
    exit 1
fi

# Create combined file with document content followed by query
COMBINED_FILE=$(mktemp)

# Add document content
cat "$CACHE_PATH" > "$COMBINED_FILE"

# Add separator and user query
echo -e "\n\n[INST] Based on the document above, please answer: $QUERY_CONTENT [/INST]" >> "$COMBINED_FILE"

# Run llama.cpp and capture its output
# CRITICAL: We must direct the output to stdout and suppress everything else
OUTPUT=$("$LLAMA_BIN" \
    -m "$MODEL_PATH" \
    -c 65536 \
    -n "$MAX_TOKENS" \
    --color -1 \
    --temp 0.7 \
    -f "$COMBINED_FILE" \
    --no-display-prompt 2>/dev/null)

# Print ONLY the model's response - this is critical for the UI to capture it
echo "$OUTPUT"

# Clean up
rm "$COMBINED_FILE"

exit 0