# Save this to a file named reset-everything.sh
#!/bin/bash
echo "=== COMPLETE RESET OF LLAMACAG UI ==="
# Kill any running instances
pkill -f "python3 main.py" || true
# Completely remove cache and config dirs
rm -rf ~/cag_project
rm -rf ~/.llamacag
# Recreate directories with proper structure
mkdir -p ~/cag_project/kv_caches
mkdir -p ~/cag_project/temp_chunks
mkdir -p ~/.llamacag/logs
# Create empty registry files
echo "{}" > ~/cag_project/kv_caches/cache_registry.json
echo "{}" > ~/cag_project/kv_caches/usage_registry.json
# Create basic config
cat > ~/.llamacag/config.json << EOF
{
  "LLAMACPP_PATH": "~/Documents/llama.cpp",
  "LLAMACPP_MODEL_DIR": "~/Documents/llama.cpp/models",
  "LLAMACPP_KV_CACHE_DIR": "~/cag_project/kv_caches",
  "LLAMACPP_TEMP_DIR": "~/cag_project/temp_chunks",
  "LLAMACPP_THREADS": "4",
  "LLAMACPP_BATCH_SIZE": "1024"
}
EOF
echo "Reset complete. Your app is ready for a fresh start."