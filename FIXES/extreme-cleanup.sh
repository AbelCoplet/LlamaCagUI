#!/bin/bash
# Complete reset of all cache-related directories and files

echo "==== Complete LlamaCag UI Reset ===="
echo "This script will completely reset your cache system."

# Get the absolute paths
HOME_DIR=$(echo ~)
CAG_DIR="$HOME_DIR/cag_project"
CONFIG_DIR="$HOME_DIR/.llamacag"
KV_CACHE_DIR="$CAG_DIR/kv_caches"
TEMP_DIR="$CAG_DIR/temp_chunks"

echo "Using following paths:"
echo "Cache directory: $KV_CACHE_DIR"
echo "Config directory: $CONFIG_DIR"

# Stop the application if it's running
if pgrep -f "python3 main.py" > /dev/null; then
    echo "Stopping running LlamaCag UI instances..."
    pkill -f "python3 main.py"
    sleep 1
fi

# Remove all cache and temp directories completely
echo "Removing cache directories..."
rm -rf "$CAG_DIR"

# Remove config directory to start fresh
echo "Removing config directory..."
rm -rf "$CONFIG_DIR"

# Recreate directories with proper permissions
echo "Creating fresh directories..."
mkdir -p "$KV_CACHE_DIR"
mkdir -p "$TEMP_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$CONFIG_DIR/logs"

# Set permissions
echo "Setting permissions..."
chmod 755 "$KV_CACHE_DIR"
chmod 755 "$TEMP_DIR"
chmod 755 "$CONFIG_DIR"

# Create basic config file
echo "Creating basic configuration..."
cat > "$CONFIG_DIR/config.json" << EOL
{
  "LLAMACPP_PATH": "$HOME_DIR/Documents/llama.cpp",
  "LLAMACPP_MODEL_DIR": "$HOME_DIR/Documents/llama.cpp/models",
  "LLAMACPP_KV_CACHE_DIR": "$KV_CACHE_DIR",
  "LLAMACPP_TEMP_DIR": "$TEMP_DIR",
  "LLAMACPP_THREADS": "4",
  "LLAMACPP_BATCH_SIZE": "1024"
}
EOL

# Create empty registry files
echo "Creating empty registry files..."
echo "{}" > "$KV_CACHE_DIR/cache_registry.json"
echo "{}" > "$KV_CACHE_DIR/usage_registry.json"

echo
echo "==== Reset Complete ===="
echo "Your LlamaCag UI has been completely reset."
echo "You will need to select your model again when you restart the application."
echo "Run ./run.sh to start the application."
echo
