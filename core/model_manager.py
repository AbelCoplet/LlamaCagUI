#!/usr/bin/env python3
"""
Model management functionality for LlamaCag UI

Handles downloading, importing, and managing large context window models.
"""

import os
import sys
import shutil
import logging
import json
import hashlib
import tempfile
import time
from pathlib import Path
import subprocess
from typing import Dict, List, Optional, Tuple

import requests
from PyQt5.QtCore import QObject, pyqtSignal


class ModelManager(QObject):
    """Manages large context window models for llama.cpp"""
    
    # Signals for UI updates
    download_progress = pyqtSignal(str, int)  # model_id, progress percentage
    download_complete = pyqtSignal(str, bool, str)  # model_id, success, message
    model_list_updated = pyqtSignal()
    import_complete = pyqtSignal(bool, str)  # success, message
    
    # Known large context window models
    KNOWN_MODELS = {
        "gemma-3-4b-128k": {
            "name": "Gemma 3 4B",
            "url": "https://huggingface.co/bartowski/gemma-4b-GGUF/resolve/main/gemma-4b-q4_k_m.gguf",
            "filename": "gemma-3-4b-128k.gguf",
            "context_window": 128000,
            "parameters": "4 billion",
            "quantization": "Q4_K_M",
            "description": "Google's smaller Gemma model, optimized for 128K context"
        },
        "deepseek-r1-7b-128k": {
            "name": "DeepSeek R1 7B",
            "url": "https://huggingface.co/TheBloke/deepseek-r1-7B-GGUF/resolve/main/deepseek-r1-7b.Q4_K_M.gguf",
            "filename": "deepseek-r1-7b-128k.gguf",
            "context_window": 128000,
            "parameters": "7 billion",
            "quantization": "Q4_K_M",
            "description": "DeepSeek's R1 model with 128K context window"
        },
        "mistral-large-2-7b-128k": {
            "name": "Mistral Large 2 7B",
            "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
            "filename": "mistral-large-2-7b-128k.gguf",
            "context_window": 128000,
            "parameters": "7 billion",
            "quantization": "Q4_K_M",
            "description": "Mistral's Large 2 model with strong reasoning"
        },
        "llama3-8b-128k": {
            "name": "Llama 3 8B",
            "url": "https://huggingface.co/TheBloke/Llama-3-8B-GGUF/resolve/main/llama-3-8b.Q4_K_M.gguf",
            "filename": "llama3-8b-128k.gguf",
            "context_window": 128000,
            "parameters": "8 billion",
            "quantization": "Q4_K_M",
            "description": "Meta's Llama 3 model with 128K context"
        }
    }
    
    def __init__(self, config):
        """Initialize model manager"""
        super().__init__()
        self.config = config
        self.models_dir = Path(os.path.expanduser(config.get('LLAMACPP_MODEL_DIR', '')))
        
        # Create models directory if it doesn't exist
        if not self.models_dir or not self.models_dir.exists():
            # Default to models directory in llamacpp path
            llamacpp_path = Path(os.path.expanduser(config.get('LLAMACPP_PATH', '~/Documents/llama.cpp')))
            self.models_dir = llamacpp_path / 'models'
            self.models_dir.mkdir(parents=True, exist_ok=True)
            
        # Cache for model metadata
        self._model_metadata = {}
        
        # Load custom model definitions if available
        self._load_custom_models()
        
    def _load_custom_models(self):
        """Load custom model definitions from user config"""
        custom_models_file = Path(self.config.get('USER_CONFIG_DIR', '~/.llamacag')) / 'custom_models.json'
        custom_models_file = Path(os.path.expanduser(custom_models_file))
        
        if custom_models_file.exists():
            try:
                with open(custom_models_file, 'r') as f:
                    custom_models = json.load(f)
                
                # Merge with known models, custom models take precedence
                for model_id, model_info in custom_models.items():
                    self.KNOWN_MODELS[model_id] = model_info
                    
                logging.info(f"Loaded {len(custom_models)} custom model definitions")
            except Exception as e:
                logging.error(f"Failed to load custom model definitions: {str(e)}")
    
    def get_available_models(self) -> List[Dict]:
        """Get list of available models on disk"""
        available_models = []
        
        for file in self.models_dir.glob("*.gguf"):
            model_id = self._get_model_id_from_filename(file.name)
            
            # Get metadata if available in known models
            metadata = self.KNOWN_MODELS.get(model_id, {})
            
            # Basic metadata from filename
            model_info = {
                "id": model_id,
                "name": metadata.get("name", file.name),
                "path": str(file),
                "filename": file.name,
                "size": file.stat().st_size,
                "context_window": metadata.get("context_window", 128000),  # Default to 128K
                "parameters": metadata.get("parameters", "Unknown"),
                "quantization": metadata.get("quantization", "Unknown"),
                "description": metadata.get("description", ""),
                "last_modified": file.stat().st_mtime
            }
            
            available_models.append(model_info)
            
            # Cache metadata for future use
            self._model_metadata[model_id] = model_info
        
        return available_models
    
    def _get_model_id_from_filename(self, filename: str) -> str:
        """Convert filename to model ID"""
        # Strip extension and cleanup
        model_id = filename.lower().replace('.gguf', '')
        
        # Match with known models if possible
        for known_id, info in self.KNOWN_MODELS.items():
            if info.get('filename', '').lower() == filename.lower():
                return known_id
        
        return model_id
    
    def get_known_models(self) -> List[Dict]:
        """Get list of known (downloadable) models"""
        models = []
        for model_id, info in self.KNOWN_MODELS.items():
            models.append({
                "id": model_id,
                "name": info.get("name", model_id),
                "context_window": info.get("context_window", 128000),
                "parameters": info.get("parameters", "Unknown"),
                "quantization": info.get("quantization", "Unknown"),
                "description": info.get("description", ""),
                "filename": info.get("filename", f"{model_id}.gguf"),
                "url": info.get("url", "")
            })
        return models
    
    def get_model_info(self, model_id: str) -> Optional[Dict]:
        """Get detailed information about a model"""
        # Check cache first
        if model_id in self._model_metadata:
            return self._model_metadata[model_id]
            
        # Check known models
        if model_id in self.KNOWN_MODELS:
            return self.KNOWN_MODELS[model_id]
            
        # Check if file exists
        model_file = self.models_dir / f"{model_id}.gguf"
        if model_file.exists():
            # Basic info from file
            info = {
                "id": model_id,
                "name": model_id,
                "path": str(model_file),
                "filename": model_file.name,
                "size": model_file.stat().st_size,
                "context_window": 128000,  # Default assumption for CAG models
                "parameters": "Unknown",
                "quantization": "Unknown",
                "description": "",
                "last_modified": model_file.stat().st_mtime
            }
            return info
            
        return None
    
    def download_model(self, model_id: str):
        """Download a model by ID"""
        if model_id not in self.KNOWN_MODELS:
            self.download_complete.emit(model_id, False, f"Unknown model ID: {model_id}")
            return
            
        model_info = self.KNOWN_MODELS[model_id]
        url = model_info.get("url")
        filename = model_info.get("filename")
        
        if not url or not filename:
            self.download_complete.emit(model_id, False, "Missing URL or filename in model info")
            return
            
        target_path = self.models_dir / filename
        
        # Start download in a separate thread to avoid blocking the UI
        import threading
        threading.Thread(
            target=self._download_model_thread,
            args=(model_id, url, target_path),
            daemon=True
        ).start()
    
    def _download_model_thread(self, model_id: str, url: str, target_path: Path):
        """Thread function for downloading a model"""
        try:
            # Create a temporary file for download
            temp_dir = tempfile.gettempdir()
            temp_file = Path(temp_dir) / f"llamacag_model_dl_{int(time.time())}.gguf.download"
            
            logging.info(f"Downloading model {model_id} from {url} to {temp_file}")
            
            # Start download with progress reporting
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Get total size if available
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            last_update = 0
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Update progress (limit updates to avoid UI flooding)
                        if total_size > 0:
                            progress = int(downloaded * 100 / total_size)
                            if progress != last_update:
                                self.download_progress.emit(model_id, progress)
                                last_update = progress
            
            # Move to final location
            shutil.move(temp_file, target_path)
            
            # Update model list and notify completion
            self.model_list_updated.emit()
            self.download_complete.emit(model_id, True, f"Model {model_id} downloaded successfully")
            
        except Exception as e:
            logging.error(f"Failed to download model {model_id}: {str(e)}")
            self.download_complete.emit(model_id, False, f"Download failed: {str(e)}")
            
            # Clean up temporary file if it exists
            if 'temp_file' in locals() and temp_file.exists():
                temp_file.unlink()
    
    def import_from_ollama(self, ollama_model: str) -> bool:
        """Import a model from Ollama"""
        try:
            # Check if Ollama is installed
            try:
                subprocess.run(["ollama", "list"], check=True, capture_output=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                self.import_complete.emit(False, "Ollama not found. Please install Ollama first.")
                return False
            
            # Get model info from Ollama
            result = subprocess.run(
                ["ollama", "show", ollama_model], 
                check=True, 
                capture_output=True, 
                text=True
            )
            
            # Extract model path from output
            model_path = None
            for line in result.stdout.splitlines():
                if "Model path:" in line:
                    model_path = line.split("Model path:", 1)[1].strip()
                    break
            
            if not model_path or not Path(model_path).exists():
                self.import_complete.emit(False, f"Could not find model path for {ollama_model}")
                return False
                
            # Copy model to our models directory
            model_file = Path(model_path)
            target_name = f"ollama_{ollama_model}.gguf"
            target_path = self.models_dir / target_name
            
            logging.info(f"Importing Ollama model from {model_path} to {target_path}")
            shutil.copy2(model_file, target_path)
            
            # Add to custom models
            model_id = f"ollama-{ollama_model}"
            custom_model = {
                "name": f"Ollama: {ollama_model}",
                "filename": target_name,
                "context_window": 128000,  # Default assumption
                "parameters": "Unknown",
                "quantization": "Unknown",
                "description": f"Imported from Ollama: {ollama_model}"
            }
            
            self._add_custom_model(model_id, custom_model)
            
            # Update model list and notify completion
            self.model_list_updated.emit()
            self.import_complete.emit(True, f"Successfully imported {ollama_model} from Ollama")
            return True
            
        except Exception as e:
            logging.error(f"Failed to import from Ollama: {str(e)}")
            self.import_complete.emit(False, f"Import failed: {str(e)}")
            return False
    
    def _add_custom_model(self, model_id: str, model_info: Dict):
        """Add a custom model definition"""
        custom_models_file = Path(self.config.get('USER_CONFIG_DIR', '~/.llamacag')) / 'custom_models.json'
        custom_models_file = Path(os.path.expanduser(custom_models_file))
        
        # Ensure directory exists
        custom_models_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing models or create new
        custom_models = {}
        if custom_models_file.exists():
            try:
                with open(custom_models_file, 'r') as f:
                    custom_models = json.load(f)
            except Exception as e:
                logging.error(f"Failed to load custom models: {str(e)}")
        
        # Add/update model
        custom_models[model_id] = model_info
        
        # Save back
        try:
            with open(custom_models_file, 'w') as f:
                json.dump(custom_models, f, indent=2)
                
            # Update in-memory list
            self.KNOWN_MODELS[model_id] = model_info
            
        except Exception as e:
            logging.error(f"Failed to save custom model: {str(e)}")
