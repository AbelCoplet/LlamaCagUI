### Screenshots

![Screenshot 2025-03-25 at 22.42.34](images/Screenshot%202025-03-25%20at%2022.42.34.png)
![Screenshot 2025-03-25 at 22.42.41](images/Screenshot%202025-03-25%20at%2022.42.41.png)
![Screenshot 2025-03-25 at 22.42.51](images/Screenshot%202025-03-25%20at%2022.42.51.png)
![Screenshot 2025-03-25 at 22.42.56](images/Screenshot%202025-03-25%20at%2022.42.56.png)
![Screenshot 2025-03-25 at 22.43.12](images/Screenshot%202025-03-25%20at%2022.43.12.png)

LlamaCag UI Enhancement Plan

```markdown

LlamaCagUI/
├── main.py                  # Application entry point, initializes all components
├── run.sh                   # Script to run the application with correct environment
├── setup_requirements.sh    # Installs dependencies, llama.cpp, and creates directories
├── README.md                # Project documentation (to be updated)
├── model_urls.txt           # List of model download URLs
├── .gitattributes           # Git attributes configuration
├── .gitignore               # Files to ignore in Git repository
│
├── core/                    # Core functionality components
│   ├── __init__.py          # Package initialization
│   ├── cache_manager.py     # Manages KV caches, listing, purging and registry
│   ├── chat_engine.py       # Handles chat interaction with models using KV caches
│   ├── document_processor.py # Processes documents into KV caches, estimates tokens
│   ├── llama_manager.py     # Manages llama.cpp installation and updates
│   ├── model_manager.py     # Handles model downloading, importing, and selection
│   └── n8n_interface.py     # Interface for n8n workflow integration
│
├── ui/                      # User interface components
│   ├── __init__.py          # Package initialization
│   ├── main_window.py       # Main application window with tabbed interface
│   ├── model_tab.py         # UI for model management and downloading
│   ├── document_tab.py      # UI for document processing and cache creation
│   ├── chat_tab.py          # UI for chatting with documents
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
│   └── token_counter.py     # Utilities for estimating tokens in documents
│
└── fixes/                   # Folder for backup and fix scripts (to be created)
    ├── [All backup files]
    └── [All diagnostic and fix scripts]
```

# LlamaCag UI

![LlamaCag Logo](https://via.placeholder.com/800x200?text=LlamaCag+UI)

## Context-Augmented Generation for Large Language Models

LlamaCag UI is a desktop application that enables context-augmented generation (CAG) with large language models. It allows you to feed entire documents into a language model's context window and ask questions that leverage that full context, creating an experience similar to chatting with your documents with unprecedented accuracy.

## 📋 Table of Contents

- [Core Concept](#core-concept)
- [Key Features](#key-features)
- [Screenshots](#screenshots)
- [Installation](#installation)
- [Usage Guide](#usage-guide)
- [Technical Details](#technical-details)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [License and Credits](#license-and-credits)

## 🧠 Core Concept

The fundamental idea behind LlamaCag UI is **Context-Augmented Generation (CAG)**, leveraging the power of `llama.cpp`'s KV (Key/Value) caching mechanism. Unlike standard RAG (Retrieval-Augmented Generation) systems that retrieve snippets of text, CAG:

1. **Processes the entire document** through the language model once to generate its internal state (the KV cache)
2. **Saves this KV cache** to disk
3. **Loads the saved KV cache** for subsequent interactions, allowing the model to "remember" the document context without re-processing the full text
4. **Enables deep contextual understanding** by having the model's state primed with the document content
5. **Allows fast follow-up questions** as only the new query needs to be processed by the model

This approach allows models like Gemma 3 and Llama 3 to efficiently utilize their large context windows (e.g., 128K tokens) for in-depth document analysis and question answering, significantly speeding up conversations after the initial document processing.

## ✨ Key Features

- **Model Management**: Download, manage, and select from various large context window models (GGUF format)
- **Document Processing**: Load documents and process them into true `llama.cpp` KV caches for efficient context augmentation
- **Interactive Chat**: Chat with your documents, leveraging the pre-processed KV cache for fast responses
- **KV Cache Monitor**: Track and manage your document KV caches
- **Settings**: Configure paths, model parameters (threads, batch size, GPU layers), and application behavior

## 📷 Screenshots

![Model Management](https://via.placeholder.com/800x450?text=Model+Management)
![Document Processing](https://via.placeholder.com/800x450?text=Document+Processing) 
![Chat Interface](https://via.placeholder.com/800x450?text=Chat+Interface)
![KV Cache Monitor](https://via.placeholder.com/800x450?text=KV+Cache+Monitor)
![Settings](https://via.placeholder.com/800x450?text=Settings)

## 🚀 Installation

### Prerequisites

- macOS, Linux, or Windows with Python 3.8+
- 16GB+ RAM recommended for optimal performance
- Internet connection (for downloading models)

### Memory Requirements

- 8GB RAM: Limited to smaller documents (~25K tokens)
- 16GB RAM: Handles documents up to ~75K tokens
- 32GB+ RAM: Required for utilizing full 128K context window

### Quick Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/LlamaCagUI.git
cd LlamaCagUI

# Run the setup script
chmod +x setup_requirements.sh
./setup_requirements.sh

# Run the application
./run.sh
```

### Manual Installation

If you prefer to install manually:

1. **Install Python dependencies**:
   ```bash
   pip install PyQt5 requests python-dotenv llama-cpp-python
   ```

2. **Set up llama.cpp**:
   ```bash
   mkdir -p ~/Documents/llama.cpp
   git clone https://github.com/ggerganov/llama.cpp.git ~/Documents/llama.cpp
   cd ~/Documents/llama.cpp
   mkdir -p build
   cd build
   cmake ..
   cmake --build . -j $(nproc)
   mkdir -p ~/Documents/llama.cpp/models
   ```

3. **Create necessary directories**:
   ```bash
   mkdir -p ~/.llamacag/logs
   mkdir -p ~/cag_project/kv_caches
   mkdir -p ~/cag_project/temp_chunks
   ```

## 📝 Usage Guide

### First-Time Setup

1. **Start the application**:
   ```bash
   ./run.sh
   ```

2. **Download a model**: 
   - Go to the Models tab
   - Click "Download Model"
   - Select a model (Gemma 3 4B Instruct recommended for beginners)
   - Wait for the download to complete

3. **Verify installation**:
   - Check that the model appears in the Models tab
   - Select the model by clicking on it

### Processing Documents (Creating a KV Cache)

1. Go to the **Documents** tab
2. Click **Select File** to choose a document (`.txt`, `.md`, etc.)
3. The app estimates the token count and indicates if it fits the current model's context window
4. Click **Create KV Cache**. This processes the document's tokens and saves the resulting model state (the KV cache) to a `.llama_cache` file
5. Optionally check "Set as Master KV Cache" to make this the default cache for new chats

### Chatting with Documents (Using a KV Cache)

1. Go to the **Chat** tab
2. Ensure **Use KV Cache** is checked. The currently selected or master KV cache will be loaded
3. Type your question about the document in the input field
4. Click **Send**. The application loads the KV cache and processes *only your query*, resulting in a fast response that leverages the document's context
5. Continue the conversation with follow-up questions, which remain fast as the document context is already loaded via the cache
6. Adjust temperature and max tokens settings as needed

### Managing KV Caches

1. Go to the **KV Cache Monitor** tab to view and manage your document caches
2. Select a cache and click **Use Selected** to switch to a different document for your current chat
3. Click **Purge Selected** to delete a cache you no longer need
4. Click **Purge All** to remove all caches and start fresh
5. Use **Refresh** to update the cache list after external changes

## 🔍 Technical Details

### How Context-Augmented Generation Works

LlamaCag UI uses `llama-cpp-python` for true KV caching:

1. **Cache Creation**:
   - When you process a document, the application loads the selected language model
   - The document text is tokenized
   - The model processes these tokens (`llm.eval(tokens)`), populating its internal Key/Value state
   - This internal state is saved to disk as a `.llama_cache` file (`llm.save_state(...)`)

2. **Chatting with Cache**:
   - When you start a chat with "Use KV Cache" enabled, the application loads the model
   - It then loads the pre-computed state from the selected `.llama_cache` file (`llm.load_state(...)`)
   - Your query is tokenized and processed (`llm.eval(query_tokens)` or `llm.create_completion(...)`). Since the document context is already in the model's state via the cache, only the query needs processing, making responses much faster

### Directory Structure

LlamaCag UI creates and uses the following directories:

- **~/.llamacag/**: Configuration directory
  - **logs/**: Log files for troubleshooting
  - **config.json**: User configuration

- **~/Documents/llama.cpp/**: llama.cpp installation
  - **models/**: Downloaded model files (.gguf)

- **~/cag_project/**: Working directories
  - **kv_caches/**: Document caches
  - **temp_chunks/**: Temporary files used during processing

## 🛠️ Troubleshooting

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

#### "KV cache not found" or "Invalid KV Cache"

**Cause**: The document hasn't been processed, the `.llama_cache` file is missing, or it's incompatible with the current model/settings.

**Solution**:
1. Process the document again using the **Documents** tab with the desired model selected
2. Check if the `.llama_cache` file exists in `~/cag_project/kv_caches/` (or your configured path)
3. Ensure the model selected in the **Models** tab is the same one used to create the cache
4. Try purging the cache via the **KV Cache Monitor** and re-processing the document

### Reset and Diagnostics

If you encounter persistent issues:

```bash
# Create a fresh configuration
rm -rf ~/.llamacag
rm -rf ~/cag_project/kv_caches
rm -rf ~/cag_project/temp_chunks
mkdir -p ~/.llamacag/logs
mkdir -p ~/cag_project/kv_caches
mkdir -p ~/cag_project/temp_chunks
```

### Debug Logs

Log files are stored in `~/.llamacag/logs/` with timestamps. When troubleshooting, check the most recent log file for detailed error information.

## ❓ FAQ

### Q: What types of documents work best with LlamaCag?
**A:** Text-based documents like `.txt`, `.md`, technical documentation, manuals, research papers, and books work best. The application excels with structured, information-rich content where context is important.

### Q: How large a document can I process?
**A:** This depends on your model's context window and available RAM. With 16GB RAM and Gemma 3 4B, you can typically process documents up to ~75K tokens. With 32GB+ RAM, you can utilize the full 128K context window. Documents that exceed the context window will be truncated.

### Q: Can I use different models with the same KV cache?
**A:** No, KV caches are specific to the model they were created with. If you switch models, you'll need to reprocess your documents to create new caches.

### Q: Does this work on Windows/Linux?
**A:** Yes, though the application was primarily tested on macOS. The core functionality should work on Windows and Linux as long as Python and the required dependencies are installed.

### Q: Does it support GPU acceleration?
**A:** Yes, GPU acceleration can be enabled by setting the GPU Layers parameter in the Settings tab. This requires `llama-cpp-python` to be installed with the correct GPU support (e.g., Metal for macOS, CUDA for Nvidia).

## 📚 Known Limitations

- **Document Size**: Documents larger than the model's context window will be truncated
- **File Types**: Best support for plain text (.txt) and markdown (.md) files
- **Memory Usage**: Large models and documents require significant RAM
- **Performance**: Initial KV cache creation can be slow for large documents. Chat responses using the cache are significantly faster. Performance depends on CPU/GPU capabilities.
- **Cache Compatibility**: KV caches are specific to the model file they were created with. Using a cache created with a different model may lead to errors or unexpected behavior.
- **Multiple Documents**: Currently limited to one document context per conversation (via a single KV cache).

## 🔮 Future Improvements

- Advanced document processing with chunking for very large documents
- Multiple document support for combining context from several sources
- PDF and Word document parsing improvements
- Custom prompt templates for different use cases
- Web UI version for remote access
- Vector database integration for hybrid RAG+CAG approaches
- Cache organization with folders and tagging
- Batch processing of document directories
- GPU layer configuration through the UI Settings tab

# Comparison: True KV Cache vs. Manual Context Prepending

Current Implementation

## 1. True KV Cache Method

```python
# In chat_engine.py
def _inference_thread_with_true_kv_cache(self, message: str, model_path: str, context_window: int,
                     kv_cache_path: Optional[str], max_tokens: int, temperature: float):
    # Load model state
    with open(kv_cache_path, 'rb') as f_pickle:
        state_data = pickle.load(f_pickle)
    llm.load_state(state_data)
    
    # Tokenize and evaluate user input
    llm.eval(input_tokens)
    
    # Generate response using loaded state
    # [generation code...]
```

This method:
- Saves the model's internal state after processing a document
- Loads this internal state directly when querying
- Preserves the full token-level representation of the document
- Optimizes for multiple queries using the same context

## 2. Manual Context Prepending (Fallback)

```python
# In chat_engine.py
def _inference_thread_fallback(self, message: str, model_path: str, context_window: int,
                    kv_cache_path: Optional[str], max_tokens: int, temperature: float, llm: Optional[Llama] = None):
    # Find original document associated with cache
    if kv_cache_path:
        cache_info = self.cache_manager.get_cache_info(kv_cache_path)
        if cache_info and 'original_document' in cache_info:
            original_doc_path_str = cache_info['original_document']
            with open(original_doc_path, 'r', encoding='utf-8', errors='replace') as f_doc:
                doc_context_text = f_doc.read(8000)
                
    # Insert document text into system prompt
    system_prompt_content = (
         f"Use the following text to answer the user's question:\n"
         f"--- TEXT START ---\n"
         f"{doc_context_text}...\n"
         f"--- TEXT END ---\n\n"
         f"Answer based *only* on the text provided above."
    )
    
    # Create chat completion with this augmented prompt
    # [generation code...]
```

This method:
- Reads the beginning of the original document (up to 8000 characters)
- Inserts this text directly into the system prompt
- Reprocesses the context with every query
- Simpler implementation with fewer dependencies on model internals

## Comparative Analysis

### Performance Comparison in CURRENT config

| Aspect | True KV Cache | Manual Context Prepending |
|--------|--------------|--------------------------|
| Setup cost | High (full document processing) | Low (file reading only) |
| Query latency | Lower (reuses processed state) | Higher (reprocesses context every time) |
| Multi-turn efficiency | Excellent (state persists) | Poor (repeats context processing) |
| Memory usage | Higher (stores full KV state) | Lower (only stores text) |
| Context capacity | Full context window | Limited to ~8000 chars (~2000 tokens) |

### Use Case Suitability

For one-shot queries, the manual context prepending offers a reasonable trade-off. It's:

1. **Simpler to implement**: No need for complex state management
2. **More robust**: Less dependent on specific model versions or implementation details
3. **Sufficient for basic needs**: For single questions about a document, prepending works well

For multi-turn conversations or very large documents, the true KV cache method would be significantly more efficient.

## Implementation as an Optional Feature

To make both methods available as options:

```python
# In settings_tab.py
def setup_ui(self):
    # Existing UI elements...
    
    # Add context method selection
    self.context_method_group = QGroupBox("Context Method")
    context_layout = QVBoxLayout(self.context_method_group)
    
    self.true_kv_radio = QRadioButton("True KV Cache (Faster for multiple queries)")
    self.manual_context_radio = QRadioButton("Manual Context Prepending (Simpler, good for one-shot queries)")
    
    if self.config.get('USE_TRUE_KV_CACHE', True):
        self.true_kv_radio.setChecked(True)
    else:
        self.manual_context_radio.setChecked(True)
    
    context_layout.addWidget(self.true_kv_radio)
    context_layout.addWidget(self.manual_context_radio)
    
    model_layout.addRow(self.context_method_group)
```

```python
# Add to save_settings method
def save_settings(self):
    # Existing code...
    
    # Save context method
    self.config['USE_TRUE_KV_CACHE'] = self.true_kv_radio.isChecked()
```

This would allow users to explicitly choose between methods based on their use case.

## Conclusion

Both approaches have their place, and having them both available gives users flexibility:

- **True KV Cache**: For power users, multiple queries, large documents
- **Manual Context Prepending**: For simpler use cases, one-shot queries, or situations where true KV caching has compatibility issues

The current implementation cleverly falls back to manual context prepending when true KV caching isn't available, but making it an explicit choice would give users more control over the performance/simplicity trade-off.


## 🌟 License and Credits

### Components and Libraries
The application uses several open-source components:
- `llama-cpp-python` library and the underlying `llama.cpp` by ggerganov and contributors
- PyQt5 for the UI framework
- Various language models (Gemma, Llama, Mistral) from their respective creators

### License
[Your license information here]

---

*LlamaCag UI: Your documents, augmented by AI.*
