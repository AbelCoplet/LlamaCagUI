# LlamaCag UI

## Context-Augmented Generation for Large Language Models

LlamaCag UI is a desktop application that enables context-augmented generation (CAG) with large language models. It allows you to feed documents into a language model's context window and ask questions that leverage that context, creating an experience similar to chatting with your documents.

## Core Concept: Context-Augmented Generation (CAG)

The fundamental idea behind LlamaCag UI is **Context-Augmented Generation (CAG)**. Unlike standard RAG (Retrieval-Augmented Generation) systems that retrieve snippets of text, CAG takes advantage of the extended context windows in modern language models by:

1. **Storing entire documents** directly in the model's context window
2. **Enabling deep contextual understanding** by giving the model the full document to work with
3. **Removing the retrieval limitations** that come with vector similarity searches
4. **Allowing follow-up questions** without having to re-retrieve information

This approach allows models like Gemma 3 and Llama 3 to leverage their 128K token context capabilities for in-depth document analysis and question answering.

## Features

- **Model Management**: Download, manage, and select from various large context window models
- **Document Processing**: Load and prepare documents as "KV caches" for context-augmented generation
- **Interactive Chat**: Chat with your documents using the power of large language models
- **KV Cache Monitor**: Track and manage your document caches
- **Settings**: Configure paths, model parameters, and application behavior

### Screenshots

![Screenshot 2025-03-25 at 22.42.34](images/Screenshot%202025-03-25%20at%2022.42.34.png)
![Screenshot 2025-03-25 at 22.42.41](images/Screenshot%202025-03-25%20at%2022.42.41.png)
![Screenshot 2025-03-25 at 22.42.51](images/Screenshot%202025-03-25%20at%2022.42.51.png)
![Screenshot 2025-03-25 at 22.42.56](images/Screenshot%202025-03-25%20at%2022.42.56.png)
![Screenshot 2025-03-25 at 22.43.12](images/Screenshot%202025-03-25%20at%2022.43.12.png)

## Installation

# LlamaCag UI Complete File Structure

```
LlamaCagUI/
├── main.py                  # Application entry point, initializes all components
├── run.sh                   # Script to run the application with correct environment
├── setup_requirements.sh    # Installs all dependencies, llama.cpp, and creates directories
├── cleanup_and_fix.sh       # Utility to clean up installation issues
├── diagnose.sh              # Diagnostic tool to check for proper installation
├── reset.sh                 # Resets application settings to defaults
├── debug_subprocess.py      # Utility for debugging subprocess calls
├── test_app.py              # Simple PyQt test application
├── .env                     # Environment variables and configuration
├── .env.example             # Example configuration file
├── model_urls.txt           # List of model download URLs
├── .gitattributes           # Git attributes configuration
├── .gitignore               # Files to ignore in Git repository
│
├── core/                    # Core functionality components
│   ├── __init__.py          # Package initialization
│   ├── cache_manager.py     # Manages KV caches, including listing, purging and registry
│   ├── chat_engine.py       # Handles chat interaction with models using KV caches
│   ├── document_processor.py # Processes documents into KV caches, estimates tokens
│   ├── llama_manager.py     # Manages llama.cpp installation and updates
│   ├── model_manager.py     # Handles model downloading, importing, and selection
│   └── n8n_interface.py     # Interface for optional n8n workflow integration
│
├── ui/                      # User interface components
│   ├── __init__.py          # Package initialization
│   ├── main_window.py       # Main application window with tabbed interface
│   ├── model_tab.py         # UI for model management and downloading
│   ├── document_tab.py      # UI for document processing and cache creation
│   ├── chat_tab.py          # UI for chatting with documents
│   ├── chat_tab.py.backup   # Backup of chat tab implementation
│   ├── cache_tab.py         # UI for KV cache monitoring and management
│   ├── settings_tab.py      # UI for application configuration
│   │
│   └── components/          # Reusable UI components
│       ├── __init__.py      # Package initialization
│       └── toast.py         # Toast notification component for temporary messages
│
├── utils/                   # Utility functions
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration management for app settings
│   ├── logging_utils.py     # Logging setup and utilities
│   ├── script_runner.py     # Utility for running external scripts with progress tracking
│   └── token_counter.py     # Utilities for estimating tokens in documents
│
└── scripts/                 # External scripts
    └── bash/
        ├── create_kv_cache.sh # Creates KV cache from a document for use with models
        └── query_kv_cache.sh  # Queries a model with a document KV cache
```

## Runtime-Created Directories (Not in Repository)

```
~/.llamacag/                 # User configuration directory
├── logs/                    # Application log files with timestamps
├── config.json              # User-specific configuration
└── custom_models.json       # User-defined model configurations

~/Documents/llama.cpp/       # llama.cpp installation directory
├── build/                   # Compiled binaries
│   └── bin/                 # Contains main or llama-cli executables
├── models/                  # Downloaded model files (.gguf format)
└── ... (other llama.cpp files)

~/cag_project/               # Working directory for documents and caches
├── kv_caches/               # Stores document KV caches
│   ├── *.bin                # Binary cache files
│   ├── *.json               # Corresponding metadata files
│   ├── master_cache.bin     # Default cache used when none selected
│   ├── cache_registry.json  # Registry of all cache files
│   ├── usage_registry.json  # Usage statistics for caches
│   └── document_registry.json # Maps documents to caches
└── temp_chunks/             # Temporary files used during processing
```

### Prerequisites

- macOS (tested on macOS Ventura and later)
- Python 3.8 or higher
- 16GB+ RAM recommended for optimal performance
- Internet connection (for downloading models)

### Memory Requirements

- 8GB RAM: Limited to smaller documents (~25K tokens)
- 16GB RAM: Handles documents up to ~75K tokens
- 32GB+ RAM: Required for utilizing full 128K context window

### Installing Dependencies

```bash
# Required Python dependencies
pip install PyQt5 requests python-dotenv

# Optional dependencies for enhanced functionality
pip install tiktoken PyPDF2 python-docx
```

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/LlamaCagUI.git
   cd LlamaCagUI
   ```

2. **Set up the environment**:
   ```bash
   # Make scripts executable
   chmod +x run.sh
   chmod +x scripts/bash/create_kv_cache.sh
   chmod +x scripts/bash/query_kv_cache.sh
   
   # Install requirements
   # Note: setup_requirements.sh will install Homebrew if not already installed
   # You may be prompted for your password during installation
   ./setup_requirements.sh
   ```

3. **Run the application**:
   ```bash
   ./run.sh
   ```

### Verifying Installation

After installation, verify that everything is working correctly:

1. **Run the diagnostics script**:
   ```bash
   ./diagnose.sh
   ```
   This will check for all dependencies and required directories.

2. **Check llama.cpp installation**:
   ```bash
   # Verify llama.cpp is built correctly
   ls ~/Documents/llama.cpp/build/bin
   ```
   You should see `main` or `llama-cli` executable.

3. **Test application launch**:
   Run `./run.sh` and confirm the application opens without errors.

## Directory Structure

LlamaCag UI creates and uses the following directories:

- **~/.llamacag/**: Configuration directory
  - **logs/**: Log files for troubleshooting
  - **config.json**: User configuration
  - **custom_models.json**: Custom model definitions

- **~/Documents/llama.cpp/**: llama.cpp installation
  - **models/**: Downloaded model files (.gguf)

- **~/cag_project/**: Working directories
  - **kv_caches/**: Document caches
  - **temp_chunks/**: Temporary files used during processing

## Usage Guide

### First-Time Setup

1. **Install llama.cpp**: If not already installed, the app will prompt you to install it
2. **Download a model**: Go to the Models tab and download one of the provided models (Gemma 3 4B Instruct recommended)

### Processing Documents

1. Go to the **Documents** tab
2. Click **Select File** to choose a document to process
3. The app will automatically estimate the token count and indicate if it fits in the model's context window
4. Click **Create KV Cache** to process the document
5. Optionally check "Set as Master KV Cache" to set it as the default document for querying

### Chatting with Documents

1. Go to the **Chat** tab
2. Make sure **Use KV Cache** is checked (enabled by default)
3. Type your question about the document in the input field
4. Click **Send** to get a response that leverages the document's context
5. Continue the conversation with follow-up questions
6. Adjust temperature and max tokens settings as needed for different response styles

### Managing KV Caches

1. Go to the **KV Cache Monitor** tab to view and manage your document caches
2. Select a cache and click **Use Selected** to switch to a different document for your current chat
3. Click **Purge Selected** to delete a cache you no longer need
4. Click **Purge All** to remove all caches and start fresh
5. Use **Refresh** to update the cache list after external changes

## File Management

### Document Caches

KV caches are stored in `~/cag_project/kv_caches/` by default. Each cache consists of:
- A `.bin` file containing the document content
- A `.json` file with metadata about the document

### Cache Registry Files

Three registry files track cache information:
- `cache_registry.json`: Maps cache files to metadata
- `usage_registry.json`: Tracks usage statistics for each cache
- `document_registry.json`: Maps documents to their caches

### Cache Management Operations

- **Viewing Caches**: The KV Cache Monitor tab shows all available caches with details
- **Selecting a Cache**: Use the "Use Selected" button to make a cache active for chat
- **Deleting Caches**: "Purge Selected" removes a single cache, "Purge All" removes all caches
- **Setting a Master Cache**: In the Documents tab, check "Set as Master KV Cache" when processing a document to make it the default

### Temporary Files

Temporary files created during processing are stored in `~/cag_project/temp_chunks/` and can be safely deleted if you need to free up space.

## Model Management

### Downloading Models

1. Go to the **Models** tab
2. Click **Download Model** to see available models
3. Select a model and click **Download Selected Model**
4. Wait for the download to complete

### Model Recommendations

- **Gemma 3 4B Instruct (Q4_K_M)**: Best balance of performance and memory usage (recommended)
- **Llama 3 8B Instruct**: Higher quality responses for more complex documents
- **Mistral 7B Instruct**: Good alternative with strong reasoning capabilities

### Manual Download

If the automatic download fails:
1. Go to the Models tab and click **Manual Download Info**
2. Follow the instructions to download and place the model files manually
3. Click **Refresh** to detect the manually downloaded models

## Configuration

### Advanced Configuration

LlamaCag UI stores its configuration in several places:

1. **User Config**: `~/.llamacag/config.json` - Contains user-specific settings
2. **Environment Variables**: `.env` file in the application directory
3. **Cache Registry**: `~/cag_project/kv_caches/cache_registry.json` - Metadata about KV caches

To modify advanced settings not available in the UI:

1. Close the application
2. Edit `~/.llamacag/config.json`
3. Restart the application

### Paths

All paths can be configured in the Settings tab:
- **llama.cpp Path**: Location of the llama.cpp installation
- **Models Path**: Directory where models are stored
- **KV Cache Path**: Directory where document caches are stored
- **Temp Path**: Directory for temporary files during processing

### Model Parameters

- **Threads**: Number of CPU threads to use for inference (default: 4)
- **Batch Size**: Batch size for processing (default: 1024)

### n8n Integration

LlamaCag UI includes optional integration with n8n for workflow automation:
- Configure n8n host and port in the Settings tab
- Use the start/stop controls to manage the n8n service
- This feature is optional and not required for core functionality

## Troubleshooting

### Common Issues

#### "No output received from model"

**Cause**: The model might be entering interactive mode or failing to generate output.

**Solution**: 
1. Check the debug logs in ~/.llamacag/logs/
2. Try a shorter document or smaller model
3. Ensure you have sufficient memory (16GB+ recommended)

#### "Model not found"

**Cause**: The model file path is incorrect or the model hasn't been downloaded.

**Solution**:
1. Go to the Models tab and download the model
2. Or manually download and place the model in the ~/Documents/llama.cpp/models/ directory

#### "KV cache not found"

**Cause**: The document hasn't been processed or the cache file is missing.

**Solution**:
1. Process the document in the Documents tab
2. Check if the cache exists in ~/cag_project/kv_caches/

### Reset and Diagnostics

If you encounter persistent issues:

```bash
# Run diagnostics
./diagnose.sh

# Reset settings
./reset.sh

# For a complete reset, you can also run:
./cleanup_and_fix.sh
```

### Debug Logs

Log files are stored in `~/.llamacag/logs/` with timestamps. When troubleshooting, check the most recent log file for detailed error information.

If reporting issues, please include the relevant log files.

## Technical Details

### How Context-Augmented Generation Works in LlamaCag

In LlamaCag UI, document content is loaded in its entirety into the model's context window. When you ask a question:

1. The document content is combined with your query in a single prompt
2. The LLM processes this combined input within its context window
3. The model can "see" and reason about the entire document, not just relevant snippets
4. This enables deeper understanding and more accurate answers

### Document Processing

When processing a document:
1. The document is analyzed to estimate token count
2. If it exceeds the model's context window, it's automatically trimmed
3. The content is stored in a "KV cache" file (.bin)
4. Metadata about the document is stored in a corresponding .json file

### Under the Hood

- The application uses llama.cpp for inference
- Documents are prepared with correctly formatted prompts for the selected model
- The query_kv_cache.sh script handles the interaction between the document and model
- PyQt5 provides the graphical interface

## Known Limitations

- **Document Size**: Documents larger than the model's context window will be truncated
- **File Types**: Best support for plain text (.txt) and markdown (.md) files
- **Memory Usage**: Large models and documents require significant RAM
- **Performance**: Processing speed depends on your CPU/GPU capabilities
- **GPU Support**: Currently optimized for CPU usage; GPU acceleration requires manual configuration
- **Multiple Documents**: Currently limited to one document per conversation

## Future Improvements

- [ ] Advanced document processing with chunking for very large documents
- [ ] Multiple document support for combining context from several sources
- [ ] PDF and Word document parsing improvements
- [ ] Custom prompt templates for different use cases
- [ ] Web UI version for remote access
- [ ] Vector database integration for hybrid RAG+CAG approaches
- [ ] Cache organization with folders and tagging
- [ ] Batch processing of document directories
- [ ] GPU acceleration configuration through the UI
- [ ] Export and import of conversations with context
- [ ] Improved document content visualization

## License and Credits


The application uses several open-source components:
- llama.cpp by ggerganov
- PyQt5 for the UI framework
- Various language models (Gemma, Llama, Mistral) from their respective creators

## Feedback and Contributions

Feedback and contributions are welcome! Please submit issues and pull requests on GitHub.

---

*LlamaCag UI: Your documents, augmented by AI.*