#!/bin/bash
# Script to clean up and fix recursive cache directory issues

echo "==== LlamaCag UI Cache Cleanup ===="
echo "This script will clean up your KV cache directory to fix recursion issues."
echo

# Clean up cache directory
echo "Cleaning up KV cache directory..."
rm -rf ~/cag_project/kv_caches/*

# Recreate basic structure
echo "Creating fresh cache directory structure..."
mkdir -p ~/cag_project/kv_caches

# Create empty registry files
echo "Creating empty registry files..."
echo "{}" > ~/cag_project/kv_caches/cache_registry.json
echo "{}" > ~/cag_project/kv_caches/usage_registry.json

# Check for and remove symlinks that point to parent directories
echo "Checking for symlinks that could cause recursion..."
find ~/cag_project -type l -exec sh -c 'target=$(readlink "$0"); case "$target" in *cag_project*) echo "Removing recursive symlink: $0"; rm "$0";; esac' {} \;

# Check config file
CONFIG_FILE=~/.llamacag/config.json
echo "Checking configuration..."
if [ -f "$CONFIG_FILE" ]; then
    # Make a backup
    cp "$CONFIG_FILE" "${CONFIG_FILE}.backup"
    echo "Backed up config to ${CONFIG_FILE}.backup"
    
    # Ensure KV cache path is correct
    # This uses a simple sed replacement - might need adjustment for more complex config files
    sed -i'.bak' 's|"LLAMACPP_KV_CACHE_DIR": ".*"|"LLAMACPP_KV_CACHE_DIR": "~/cag_project/kv_caches"|g' "$CONFIG_FILE"
    echo "Updated KV cache path in config file"
else
    echo "Config file not found at $CONFIG_FILE"
    echo "Creating default config..."
    mkdir -p ~/.llamacag
    cat > "$CONFIG_FILE" << EOL
{
  "LLAMACPP_PATH": "~/Documents/llama.cpp",
  "LLAMACPP_MODEL_DIR": "~/Documents/llama.cpp/models",
  "LLAMACPP_KV_CACHE_DIR": "~/cag_project/kv_caches",
  "LLAMACPP_TEMP_DIR": "~/cag_project/temp_chunks"
}
EOL
fi

echo
echo "==== Cleanup Complete ===="
echo "Your KV cache directory has been reset."
echo "Please replace the core/cache_manager.py and ui/cache_tab.py files with the fixed versions."
echo "Then run ./run.sh to start the application."
echo
