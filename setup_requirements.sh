#!/bin/bash
# Helper script to set up requirements for LlamaCag UI

echo "==== LlamaCag UI Requirements Setup ===="
echo "This script will install the required dependencies for LlamaCag UI."
echo "You may be prompted for your password to install packages."
echo

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Check if Homebrew was installed successfully
    if ! command -v brew &> /dev/null; then
        echo "Failed to install Homebrew. Please install it manually and try again."
        exit 1
    fi
    
    echo "Homebrew installed successfully."
else
    echo "Homebrew is already installed."
fi

# Install required packages
echo "Installing required packages..."
brew install git cmake make python3 pyqt@5

# Install Python packages
echo "Installing required Python packages..."
pip3 install PyQt5 requests python-dotenv

# Set up llama.cpp directory
echo "Setting up llama.cpp directory..."
LLAMACPP_DIR="$HOME/Documents/llama.cpp"

if [ -d "$LLAMACPP_DIR" ]; then
    echo "llama.cpp directory exists. Updating..."
    cd "$LLAMACPP_DIR" || exit 1
    git pull
else
    echo "Creating llama.cpp directory and cloning repository..."
    mkdir -p "$LLAMACPP_DIR"
    git clone https://github.com/ggerganov/llama.cpp.git "$LLAMACPP_DIR"
    cd "$LLAMACPP_DIR" || exit 1
fi

# Build llama.cpp
echo "Building llama.cpp..."
mkdir -p build
cd build || exit 1

# Configure build
echo "Configuring build..."
cmake ..

# Build with available CPU cores
CPU_CORES=$(sysctl -n hw.ncpu)
echo "Building with $CPU_CORES cores..."
make -j "$CPU_CORES"

# Create models directory
echo "Creating models directory..."
mkdir -p "$LLAMACPP_DIR/models"

# Create directories for KV cache and temp files
echo "Creating directories for KV cache and temp files..."
mkdir -p "$HOME/cag_project/kv_caches"
mkdir -p "$HOME/cag_project/temp_chunks"

echo
echo "==== Setup Complete ===="
echo "llama.cpp has been installed to: $LLAMACPP_DIR"
echo "You can now run LlamaCag UI."
echo