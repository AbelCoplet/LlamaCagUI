#!/bin/bash
# Diagnostic script for LlamaCag UI
# This script checks if all dependencies are properly installed and configured

echo "==== LlamaCag UI Diagnostics Tool ===="
echo "This tool will check your setup and identify any issues."
echo

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1)
if [[ $python_version == *"Python 3"* ]]; then
  echo "✅ Python is installed: $python_version"
else
  echo "❌ Python 3 not found. Please install Python 3.8 or higher."
  echo "   Run: brew install python"
fi

# Check PyQt5
echo "Checking PyQt5..."
if python3 -c "import PyQt5" 2>/dev/null; then
  echo "✅ PyQt5 is installed"
else
  echo "❌ PyQt5 not found. Please install PyQt5."
  echo "   Run: pip3 install PyQt5"
fi

# Check required Python packages
echo "Checking Python packages..."
packages=("requests" "python-dotenv")
for package in "${packages[@]}"; do
  if python3 -c "import $package" 2>/dev/null; then
    echo "✅ $package is installed"
  else
    echo "❌ $package not found. Please install $package."
    echo "   Run: pip3 install $package"
  fi
done

# Check for llama.cpp
echo "Checking llama.cpp..."
LLAMACPP_PATH=~/Documents/llama.cpp
if [ -d "$LLAMACPP_PATH" ]; then
  echo "✅ llama.cpp directory exists at $LLAMACPP_PATH"
  
  # Check for main executable
  if [ -f "$LLAMACPP_PATH/build/bin/main" ] || [ -f "$LLAMACPP_PATH/build/bin/llama-cli" ]; then
    echo "✅ llama.cpp appears to be built correctly"
  else
    echo "❌ llama.cpp executable not found. It may not be properly built."
    echo "   Let the application install it, or run:"
    echo "   cd $LLAMACPP_PATH && mkdir -p build && cd build && cmake .. && make -j4"
  fi
else
  echo "❌ llama.cpp not found at $LLAMACPP_PATH"
  echo "   Let the application install it automatically."
fi

# Check models directory and models
echo "Checking models directory..."
MODELS_DIR=~/Documents/llama.cpp/models
if [ -d "$MODELS_DIR" ]; then
  echo "✅ Models directory exists at $MODELS_DIR"
  
  # Count GGUF files
  gguf_count=$(find "$MODELS_DIR" -name "*.gguf" | wc -l)
  
  if [ "$gguf_count" -gt 0 ]; then
    echo "✅ Found $gguf_count .gguf model file(s):"
    find "$MODELS_DIR" -name "*.gguf" | while read model; do
      basename=$(basename "$model")
      size=$(du -h "$model" | cut -f1)
      echo "   • $basename ($size)"
    done
  else
    echo "❌ No .gguf model files found in $MODELS_DIR"
    echo "   Download models through the application or manually."
  fi
else
  echo "❌ Models directory not found at $MODELS_DIR"
  echo "   Creating it now..."
  mkdir -p "$MODELS_DIR"
fi

# Check KV cache directory
echo "Checking KV cache directory..."
KV_CACHE_DIR=~/cag_project/kv_caches
if [ -d "$KV_CACHE_DIR" ]; then
  echo "✅ KV cache directory exists at $KV_CACHE_DIR"
  
  # Count BIN files
  bin_count=$(find "$KV_CACHE_DIR" -name "*.bin" | wc -l)
  
  if [ "$bin_count" -gt 0 ]; then
    echo "✅ Found $bin_count KV cache file(s)"
  else
    echo "ℹ️  No KV caches found. Process a document in the Documents tab."
  fi
else
  echo "ℹ️  KV cache directory not found at $KV_CACHE_DIR"
  echo "   It will be created when you process your first document."
  mkdir -p "$KV_CACHE_DIR"
fi

# Check scripts
echo "Checking scripts..."
SCRIPTS_DIR=./scripts/bash
if [ -d "$SCRIPTS_DIR" ]; then
  echo "✅ Scripts directory exists at $SCRIPTS_DIR"
  
  # Check create_kv_cache.sh
  if [ -f "$SCRIPTS_DIR/create_kv_cache.sh" ]; then
    if [ -x "$SCRIPTS_DIR/create_kv_cache.sh" ]; then
      echo "✅ create_kv_cache.sh exists and is executable"
    else
      echo "❌ create_kv_cache.sh exists but is not executable"
      echo "   Run: chmod +x $SCRIPTS_DIR/create_kv_cache.sh"
    fi
  else
    echo "❌ create_kv_cache.sh not found"
    echo "   Run: ./create_scripts_dir.sh"
  fi
  
  # Check query_kv_cache.sh
  if [ -f "$SCRIPTS_DIR/query_kv_cache.sh" ]; then
    if [ -x "$SCRIPTS_DIR/query_kv_cache.sh" ]; then
      echo "✅ query_kv_cache.sh exists and is executable"
    else
      echo "❌ query_kv_cache.sh exists but is not executable"
      echo "   Run: chmod +x $SCRIPTS_DIR/query_kv_cache.sh"
    fi
  else
    echo "❌ query_kv_cache.sh not found"
    echo "   Run: ./create_scripts_dir.sh"
  fi
else
  echo "❌ Scripts directory not found at $SCRIPTS_DIR"
  echo "   Run: ./create_scripts_dir.sh"
fi

# Check configuration
echo "Checking configuration..."
if [ -f ".env" ]; then
  echo "✅ .env configuration file exists"
else
  echo "❌ .env configuration file not found"
  echo "   Creating default configuration..."
  
  cat > .env << EOL
# LlamaCag UI Configuration

# Paths
LLAMACPP_PATH=~/Documents/llama.cpp
LLAMACPP_MODEL_DIR=~/Documents/llama.cpp/models
LLAMACPP_KV_CACHE_DIR=~/cag_project/kv_caches
LLAMACPP_TEMP_DIR=~/cag_project/temp_chunks
DOCUMENTS_FOLDER=~/Documents/cag_documents

# Performance settings
LLAMACPP_THREADS=4
LLAMACPP_BATCH_SIZE=1024
LLAMACPP_MAX_CONTEXT=128000

# Using local scripts instead of external dependencies
CREATE_KV_CACHE_SCRIPT=./scripts/bash/create_kv_cache.sh
QUERY_KV_CACHE_SCRIPT=./scripts/bash/query_kv_cache.sh

# n8n integration (optional)
N8N_PROTOCOL=http
N8N_HOST=localhost
N8N_PORT=5678
EOL
  
  echo "✅ Created default .env file"
fi

# Check for user config directory
USER_CONFIG_DIR=~/.llamacag
if [ -d "$USER_CONFIG_DIR" ]; then
  echo "✅ User configuration directory exists at $USER_CONFIG_DIR"
else
  echo "ℹ️  User configuration directory not found at $USER_CONFIG_DIR"
  echo "   It will be created when you run the application."
  mkdir -p "$USER_CONFIG_DIR"
fi

echo
echo "==== Diagnostics Summary ===="
if [ -d "$LLAMACPP_PATH" ] && [ -d "$MODELS_DIR" ] && [ "$gguf_count" -gt 0 ] && [ -f "$SCRIPTS_DIR/create_kv_cache.sh" ] && [ -f "$SCRIPTS_DIR/query_kv_cache.sh" ]; then
  echo "✅ Your LlamaCag UI setup appears to be ready!"
  echo "   You can run the application with: ./run.sh"
else
  echo "⚠️  There are issues with your LlamaCag UI setup."
  echo "   Please address the issues mentioned above."
  echo "   After fixing the issues, run this script again."
fi
echo