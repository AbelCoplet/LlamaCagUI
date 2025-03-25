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
import threading
import re
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
        inference_thread = threading.Thread(
            target=self._inference_thread,
            args=(message, model_path, max_tokens, temperature),
            daemon=True
        )
        inference_thread.start()
        
        return True
    
    def _inference_thread(self, message: str, model_path: str, max_tokens: int, temperature: float):
        """Thread function for model inference with ULTRA RELIABLE output capture"""
        try:
            # Signal that response has started
            self.response_started.emit()
            
            # Create a temporary file for the prompt
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(message)
                prompt_file = f.name
            
            # Build command
            cmd = [str(self.query_kv_cache_script), str(model_path)]
            
            # Add document/cache path
            if self.use_kv_cache and self.current_kv_cache:
                cmd.append(str(self.current_kv_cache))
            else:
                # If not using KV cache, use an empty file
                dummy_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
                dummy_file.close()
                cmd.append(dummy_file.name)
            
            # Add remaining parameters
            cmd.append(f"@{prompt_file}")  # Use @file syntax for prompt
            cmd.append(str(max_tokens))
            cmd.append(str(temperature))
            
            logging.info(f"Running inference with command: {cmd}")
            
            # ULTRA RELIABLE OUTPUT CAPTURE:
            # Using subprocess.run to get complete output, then manually filtering
            try:
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False  # Don't raise error on non-zero exit
                )
                
                # Get output and error
                output = result.stdout
                error = result.stderr
                
                # Log any errors
                if error:
                    logging.warning(f"llama.cpp stderr: {error}")
                
                # Check if we have any output
                if output.strip():
                    # Process the output
                    complete_response = self._extract_answer(output)
                    
                    # Emit each line as a chunk for real-time display
                    for line in complete_response.split('\n'):
                        self.response_chunk.emit(line + '\n')
                    
                    # Add to history
                    self.history.append({"role": "assistant", "content": complete_response})
                    
                    # Update KV cache usage stats if using KV cache
                    if self.use_kv_cache and self.current_kv_cache:
                        self.cache_manager.update_usage(self.current_kv_cache)
                    
                    # Signal completion
                    self.response_complete.emit(complete_response, True)
                else:
                    # No output from model
                    error_message = "No output received from model"
                    if error:
                        error_message += f": {error}"
                    logging.error(error_message)
                    self.error_occurred.emit(error_message)
                    self.response_complete.emit("I couldn't generate a response. Please try again.", False)
            except Exception as e:
                logging.error(f"Error capturing model output: {str(e)}")
                self.error_occurred.emit(f"Error capturing model output: {str(e)}")
                self.response_complete.emit("An error occurred while processing your request.", False)
            
            # Clean up temporary files
            try:
                os.unlink(prompt_file)
                # Clean up dummy file if used
                if not self.use_kv_cache or not self.current_kv_cache:
                    os.unlink(dummy_file.name)
            except Exception as e:
                logging.warning(f"Error cleaning up temp files: {e}")
                
        except Exception as e:
            logging.error(f"Error in inference thread: {str(e)}")
            self.error_occurred.emit(f"Inference error: {str(e)}")
            self.response_complete.emit("An error occurred while processing your request.", False)
    
    def _extract_answer(self, full_output: str) -> str:
        """Extract just the answer from the full model output"""
        # First, try to find the "ANSWER:" marker and extract everything after it
        if "ANSWER:" in full_output:
            answer_section = full_output.split("ANSWER:", 1)[1].strip()
            
            # Look for end markers that might be in the output
            end_markers = ["DOCUMENT:", "QUESTION:", "You are given", "You are an AI", "<|end|>"]
            for marker in end_markers:
                if marker in answer_section:
                    answer_section = answer_section.split(marker, 1)[0].strip()
            
            return answer_section
            
        # If we can't find "ANSWER:", try to find logical sections in the output
        
        # Remove any model loading information at the beginning
        # Lines that contain typical llama.cpp loading info
        output_lines = full_output.split('\n')
        cleaned_lines = []
        skip_pattern = re.compile(r'(llama_|ggml_|system_info:|main:|build:|load:|print_info:)')
        
        started_content = False
        for line in output_lines:
            # Skip lines with typical loading info
            if skip_pattern.search(line):
                continue
                
            # If we find an empty line after content started, include it
            if started_content or line.strip():
                started_content = True
                cleaned_lines.append(line)
        
        # Join the cleaned lines
        cleaned_output = '\n'.join(cleaned_lines).strip()
        
        # If there's still our prompt in the output, try to remove it
        if "DOCUMENT:" in cleaned_output and "QUESTION:" in cleaned_output:
            # Take everything after the last occurrence of "QUESTION:"
            question_parts = cleaned_output.split("QUESTION:")
            if len(question_parts) > 1:
                # Look for the actual answer after the question
                possible_answer = question_parts[-1].strip()
                if ':' in possible_answer:
                    # Extract everything after the first colon after the question
                    answer_only = possible_answer.split(':', 1)[1].strip()
                    if answer_only:
                        return answer_only
        
        # If all else fails, return the cleaned output (or partial output if it's too long)
        if cleaned_output:
            # If output is very long, assume beginning is still prompt remnants
            if len(cleaned_output) > 2000:
                return cleaned_output[-2000:].strip()
            return cleaned_output
        
        # Last resort: return some part of the original output
        # Take last 1000 chars which are most likely to be the actual answer
        return full_output[-1000:].strip()
    
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
    
    def update_config(self, config):
        """Update configuration"""
        self.config = config
        new_script_path = Path(os.path.expanduser(
            config.get('QUERY_KV_CACHE_SCRIPT', '~/llama-cag-n8n/scripts/bash/query_kv_cache.sh')
        ))
        if new_script_path != self.query_kv_cache_script:
            self.query_kv_cache_script = new_script_path
            logging.info(f"Updated query_kv_cache_script to {self.query_kv_cache_script}")