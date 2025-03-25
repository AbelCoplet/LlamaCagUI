#!/usr/bin/env python3
"""
Chat functionality for LlamaCag UI

Handles interaction with the model using KV caches.
"""

import os
import sys
import subprocess
import tempfile
import logging
import shutil
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from PyQt5.QtCore import QObject, pyqtSignal

from utils.script_runner import run_script


class ChatEngine(QObject):
    """Chat functionality using large context window models with KV caches"""
    
    # Signals
    response_started = pyqtSignal()
    response_chunk = pyqtSignal(str)  # Text chunk
    response_complete = pyqtSignal(str, bool)  # Full response, success
    error_occurred = pyqtSignal(str)  # Error message
    
    def __init__(self, config, llama_manager, model_manager, cache_manager):
        """Initialize chat engine"""
        super().__init__()
        self.config = config
        self.llama_manager = llama_manager
        self.model_manager = model_manager
        self.cache_manager = cache_manager
        
        # Get script paths
        self.query_kv_cache_script = Path(os.path.expanduser(
            config.get('QUERY_KV_CACHE_SCRIPT', '~/llama-cag-n8n/scripts/bash/query_kv_cache.sh')
        ))
        
        # Chat history
        self.history = []
        
        # Current KV cache
        self.current_kv_cache = None
        self.use_kv_cache = True
    
    def set_kv_cache(self, kv_cache_path: Optional[Union[str, Path]]):
        """Set the current KV cache to use"""
        if kv_cache_path:
            cache_path = Path(kv_cache_path)
            if not cache_path.exists():
                logging.error(f"KV cache not found: {cache_path}")
                self.error_occurred.emit(f"KV cache not found: {cache_path}")
                return False
                
            self.current_kv_cache = str(cache_path)
            logging.info(f"Set current KV cache to {self.current_kv_cache}")
            return True
        else:
            self.current_kv_cache = None
            logging.info("Cleared current KV cache")
            return True
    
    def toggle_kv_cache(self, enabled: bool):
        """Toggle KV cache usage"""
        self.use_kv_cache = enabled
        logging.info(f"KV cache usage toggled: {enabled}")
    
    def send_message(self, message: str, max_tokens: int = 1024, temperature: float = 0.7):
        """Send a message to the model and get a response"""
        # Check if model is set
        model_id = self.config.get('CURRENT_MODEL_ID', 'gemma-3-4b-128k')
        model_info = self.model_manager.get_model_info(model_id)
        
        if not model_info:
            self.error_occurred.emit(f"No model selected. Please select a model first.")
            return False
            
        model_path = model_info.get('path')
        if not model_path or not Path(model_path).exists():
            self.error_occurred.emit(f"Model not found: {model_path}")
            return False
        
        # Check if KV cache is available when enabled
        if self.use_kv_cache:
            if not self.current_kv_cache:
                # Try to use master cache
                master_cache = Path(os.path.expanduser(
                    self.config.get('MASTER_KV_CACHE', '~/cag_project/kv_caches/master_cache.bin')
                ))
                
                if master_cache.exists():
                    self.current_kv_cache = str(master_cache)
                    logging.info(f"Using master KV cache: {self.current_kv_cache}")
                else:
                    self.error_occurred.emit("No KV cache selected and no master cache found.")
                    return False
        
        # Add to history
        self.history.append({"role": "user", "content": message})
        
        # Start inference in a separate thread
        import threading
        threading.Thread(
            target=self._inference_thread,
            args=(message, model_path, max_tokens, temperature),
            daemon=True
        ).start()
        
        return True
    
    def _inference_thread(self, message: str, model_path: str, max_tokens: int, temperature: float):
        """Thread function for model inference"""
        try:
            # Signal that response has started
            self.response_started.emit()
            
            # Create a temporary file for the prompt
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(message)
                prompt_file = f.name
            
            # Build command
            cmd = [str(self.query_kv_cache_script), str(model_path)]
            
            if self.use_kv_cache and self.current_kv_cache:
                cmd.append(str(self.current_kv_cache))
            else:
                # If not using KV cache, use a dummy argument (script requires it)
                dummy_cache = tempfile.NamedTemporaryFile(delete=False, suffix='.bin')
                dummy_cache.close()
                cmd.append(dummy_cache.name)
                # Will clean up later
            
            # Add remaining parameters
            cmd.extend([
                f"@{prompt_file}",  # Use @file syntax for prompt
                str(max_tokens),
                f"--temp {temperature}"
            ])
            
            logging.info(f"Running inference with command: {cmd}")
            
            # Create process with real-time output handling
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            # Read output in real-time
            complete_response = ""
            for line in process.stdout:
                self.response_chunk.emit(line)
                complete_response += line
            
            # Wait for process to complete
            process.wait()
            
            # Check result
            if process.returncode != 0:
                stderr = process.stderr.read()
                error_message = f"Inference failed with code {process.returncode}"
                if stderr:
                    error_message += f": {stderr}"
                    
                logging.error(error_message)
                self.error_occurred.emit(error_message)
                self.response_complete.emit("", False)
            else:
                # Add to history
                self.history.append({"role": "assistant", "content": complete_response})
                
                # Update KV cache usage stats if using KV cache
                if self.use_kv_cache and self.current_kv_cache:
                    self.cache_manager.update_usage(self.current_kv_cache)
                
                # Signal completion
                self.response_complete.emit(complete_response, True)
            
            # Clean up temporary files
            os.unlink(prompt_file)
            
            # Clean up dummy cache if used
            if not self.use_kv_cache or not self.current_kv_cache:
                try:
                    os.unlink(dummy_cache.name)
                except:
                    pass
                
        except Exception as e:
            logging.error(f"Error in inference thread: {str(e)}")
            self.error_occurred.emit(f"Inference error: {str(e)}")
            self.response_complete.emit("", False)
    
    def clear_history(self):
        """Clear chat history"""
        self.history = []
        logging.info("Chat history cleared")
    
    def get_history(self) -> List[Dict]:
        """Get chat history"""
        return self.history
    
    def save_history(self, file_path: Union[str, Path]) -> bool:
        """Save chat history to a file"""
        try:
            with open(file_path, 'w') as f:
                json.dump({
                    "history": self.history,
                    "model_id": self.config.get('CURRENT_MODEL_ID', 'gemma-3-4b-128k'),
                    "kv_cache": self.current_kv_cache,
                    "timestamp": time.time()
                }, f, indent=2)
            logging.info(f"Chat history saved to {file_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to save chat history: {str(e)}")
            return False
    
    def load_history(self, file_path: Union[str, Path]) -> bool:
        """Load chat history from a file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            self.history = data.get("history", [])
            
            # Optionally load KV cache
            kv_cache = data.get("kv_cache")
            if kv_cache and Path(kv_cache).exists():
                self.current_kv_cache = kv_cache
                
            logging.info(f"Chat history loaded from {file_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to load chat history: {str(e)}")
            return False
