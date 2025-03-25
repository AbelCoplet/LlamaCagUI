#!/bin/bash
# Script to clean up and fix LlamaCag UI

echo "==== LlamaCag UI Cleanup and Fix ===="
echo "This script will clean up your installation and fix known issues."
echo

# Determine working directory
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR" || exit 1

# Define important paths
CONFIG_DIR="$HOME/.llamacag"
LLAMACPP_DIR="$HOME/Documents/llama.cpp"
MODELS_DIR="$LLAMACPP_DIR/models"
KV_CACHE_DIR="$HOME/cag_project/kv_caches"
TEMP_DIR="$HOME/cag_project/temp_chunks"

# Ask user what to do
echo "Choose an option:"
echo "1. Clean up configuration only (saves your models and llama.cpp)"
echo "2. Complete reset (removes all settings, caches, and model references)"
echo "3. Check and fix model directory issues only"
echo "4. Exit without changes"
read -p "Enter your choice [1-4]: " choice

case $choice in
  1)
    echo "Cleaning up configuration..."
    rm -rf "$CONFIG_DIR"
    echo "Configuration cleaned up."
    ;;
  2)
    echo "Performing complete reset..."
    rm -rf "$CONFIG_DIR"
    rm -rf "$KV_CACHE_DIR"
    rm -rf "$TEMP_DIR"
    echo "Reset complete."
    ;;
  3)
    echo "Checking model directory issues only..."
    ;;
  4)
    echo "Exiting without changes."
    exit 0
    ;;
  *)
    echo "Invalid choice. Exiting."
    exit 1
    ;;
esac

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p "$CONFIG_DIR"
mkdir -p "$MODELS_DIR"
mkdir -p "$KV_CACHE_DIR"
mkdir -p "$TEMP_DIR"

# Create a basic configuration file
echo "Creating basic configuration file..."
cat > "$CONFIG_DIR/config.json" << EOL
{
  "LLAMACPP_PATH": "$LLAMACPP_DIR",
  "LLAMACPP_MODEL_DIR": "$MODELS_DIR",
  "LLAMACPP_KV_CACHE_DIR": "$KV_CACHE_DIR",
  "LLAMACPP_TEMP_DIR": "$TEMP_DIR",
  "LLAMACPP_THREADS": "4",
  "LLAMACPP_BATCH_SIZE": "1024",
  "USER_CONFIG_DIR": "$CONFIG_DIR"
}
EOL

# Check models directory
echo "Checking models directory..."
if [ -d "$MODELS_DIR" ]; then
  MODEL_COUNT=$(find "$MODELS_DIR" -name "*.gguf" | wc -l)
  if [ "$MODEL_COUNT" -gt 0 ]; then
    echo "Found $MODEL_COUNT models in $MODELS_DIR"
    find "$MODELS_DIR" -name "*.gguf" | while read -r model; do
      echo "  - $(basename "$model")"
    done
  else
    echo "No models found in $MODELS_DIR"
    echo "You will need to download models or place them manually."
  fi
else
  echo "Models directory $MODELS_DIR does not exist."
  echo "Creating it now..."
  mkdir -p "$MODELS_DIR"
fi

# Fetch correct model URLs
echo "Fetching correct model information..."
cat > model_urls.txt << EOL
Gemma 3 4B Instruct: https://huggingface.co/bartowski/google_gemma-3-4b-it-GGUF/blob/main/gemma-3-4b-it-Q4_K_M.gguf
Filename: gemma-3-4b-it-Q4_K_M.gguf
Direct download: https://huggingface.co/bartowski/google_gemma-3-4b-it-GGUF/resolve/main/gemma-3-4b-it-Q4_K_M.gguf

Gemma 3 4B Base: https://huggingface.co/bartowski/google_gemma-3-4b-GGUF/blob/main/gemma-3-4b.Q4_K_M.gguf
Filename: gemma-3-4b.Q4_K_M.gguf
Direct download: https://huggingface.co/bartowski/google_gemma-3-4b-GGUF/resolve/main/gemma-3-4b.Q4_K_M.gguf
EOL

echo "Do you want to attempt to download a model now?"
echo "1. Download Gemma 3 4B Instruct (2.49GB)"
echo "2. Skip model download"
read -p "Enter your choice [1-2]: " download_choice

if [ "$download_choice" -eq 1 ]; then
  echo "Downloading Gemma 3 4B Instruct..."
  echo "This may take some time depending on your internet connection."
  if command -v curl &>/dev/null; then
    curl -L "https://huggingface.co/bartowski/google_gemma-3-4b-it-GGUF/resolve/main/gemma-3-4b-it-Q4_K_M.gguf" -o "$MODELS_DIR/gemma-3-4b-it-Q4_K_M.gguf"
  elif command -v wget &>/dev/null; then
    wget -O "$MODELS_DIR/gemma-3-4b-it-Q4_K_M.gguf" "https://huggingface.co/bartowski/google_gemma-3-4b-it-GGUF/resolve/main/gemma-3-4b-it-Q4_K_M.gguf"
  else
    echo "Neither curl nor wget found. Please download the model manually."
  fi
fi

echo
echo "==== Cleanup and Fix Complete ===="
echo "You can now run the application with:"
echo "./run.sh"
echo
echo "If you still encounter issues, please manually download a model from the URLs in model_urls.txt"
echo "and place it in $MODELS_DIR"
echo