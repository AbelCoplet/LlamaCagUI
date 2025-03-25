#!/usr/bin/env python3
"""
Document processing functionality for LlamaCag UI

Handles document validation, token estimation, and KV cache creation.
"""

import os
import sys
import subprocess
import tempfile
import logging
import shutil
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from PyQt5.QtCore import QObject, pyqtSignal

from utils.token_counter import estimate_tokens
from utils.script_runner import run_script


class DocumentProcessor(QObject):
    """Processes documents into KV caches for large context window models"""
    
    # Signals
    processing_progress = pyqtSignal(str, int)  # document_id, progress percentage
    processing_complete = pyqtSignal(str, bool, str)  # document_id, success, message
    token_estimation_complete = pyqtSignal(str, int, bool)  # document_id, tokens, fits_context
    
    def __init__(self, config, llama_manager, model_manager, cache_manager):
        """Initialize document processor"""
        super().__init__()
        self.config = config
        self.llama_manager = llama_manager
        self.model_manager = model_manager
        self.cache_manager = cache_manager
        
        # Set up directories
        self.temp_dir = Path(os.path.expanduser(config.get('LLAMACPP_TEMP_DIR', '~/cag_project/temp_chunks')))
        self.kv_cache_dir = Path(os.path.expanduser(config.get('LLAMACPP_KV_CACHE_DIR', '~/cag_project/kv_caches')))
        
        # Ensure directories exist
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.kv_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Get script paths
        self.create_kv_cache_script = Path(os.path.expanduser(
            config.get('CREATE_KV_CACHE_SCRIPT', '~/llama-cag-n8n/scripts/bash/create_kv_cache.sh')
        ))
        
        # Document registry
        self._document_registry = {}
        self._load_document_registry()
    
    def _load_document_registry(self):
        """Load document registry from disk"""
        registry_file = self.kv_cache_dir / 'document_registry.json'
        if registry_file.exists():
            try:
                with open(registry_file, 'r') as f:
                    self._document_registry = json.load(f)
                logging.info(f"Loaded document registry with {len(self._document_registry)} entries")
            except Exception as e:
                logging.error(f"Failed to load document registry: {str(e)}")
    
    def _save_document_registry(self):
        """Save document registry to disk"""
        registry_file = self.kv_cache_dir / 'document_registry.json'
        try:
            with open(registry_file, 'w') as f:
                json.dump(self._document_registry, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save document registry: {str(e)}")
    
    def get_document_registry(self) -> Dict:
        """Get the document registry"""
        return self._document_registry
    
    def estimate_tokens(self, document_path: Union[str, Path]) -> int:
        """Estimate the number of tokens in a document"""
        document_path = Path(document_path)
        if not document_path.exists():
            raise FileNotFoundError(f"Document not found: {document_path}")
            
        document_id = self._get_document_id(document_path)
        
        try:
            # Read document content
            with open(document_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Estimate tokens
            tokens = estimate_tokens(content)
            
            # Get current model's context size
            model_id = self.config.get('CURRENT_MODEL_ID', 'gemma-3-4b-128k')
            model_info = self.model_manager.get_model_info(model_id)
            context_size = model_info.get('context_window', 128000) if model_info else 128000
            
            # Check if it fits in context
            fits_context = tokens <= context_size
            
            # Emit signal with results
            self.token_estimation_complete.emit(document_id, tokens, fits_context)
            
            return tokens
            
        except Exception as e:
            logging.error(f"Failed to estimate tokens for {document_path}: {str(e)}")
            self.token_estimation_complete.emit(document_id, 0, False)
            return 0
    
    def process_document(self, document_path: Union[str, Path], set_as_master: bool = False) -> bool:
        """Process a document into a KV cache"""
        document_path = Path(document_path)
        if not document_path.exists():
            self.processing_complete.emit("unknown", False, f"Document not found: {document_path}")
            return False
        
        document_id = self._get_document_id(document_path)
        
        try:
            # Create a temp copy of the document
            temp_file = self.temp_dir / f"{document_id}_{int(time.time())}.txt"
            shutil.copy2(document_path, temp_file)
            
            # Create KV cache path
            kv_cache_path = self.kv_cache_dir / f"{document_id}.bin"
            
            # Get current model path
            model_id = self.config.get('CURRENT_MODEL_ID', 'gemma-3-4b-128k')
            model_info = self.model_manager.get_model_info(model_id)
            
            if not model_info:
                self.processing_complete.emit(document_id, False, f"Model not found: {model_id}")
                return False
                
            model_path = model_info.get('path')
            
            # Estimate tokens for context sizing
            token_count = self.estimate_tokens(document_path)
            
            # Start processing in a separate thread
            import threading
            threading.Thread(
                target=self._process_document_thread,
                args=(document_id, model_path, temp_file, kv_cache_path, token_count, set_as_master),
                daemon=True
            ).start()
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to process document {document_path}: {str(e)}")
            self.processing_complete.emit(document_id, False, f"Processing failed: {str(e)}")
            return False
    
    def _process_document_thread(self, document_id: str, model_path: str, 
                              temp_file: Path, kv_cache_path: Path, 
                              token_count: int, set_as_master: bool):
        """Thread function for document processing"""
        try:
            # Calculate context size with some padding
            context_size = min(max(token_count + 1000, 2048), 128000)
            context_size = (context_size + 255) // 256 * 256  # Round to nearest 256
            
            # Get threads and batch size from config
            threads = int(self.config.get('LLAMACPP_THREADS', '4'))
            batch_size = int(self.config.get('LLAMACPP_BATCH_SIZE', '1024'))
            
            # Build command
            cmd = [
                str(self.create_kv_cache_script),
                str(model_path),
                str(temp_file),
                str(kv_cache_path),
                str(context_size),
                str(threads),
                str(batch_size)
            ]
            
            logging.info(f"Creating KV cache for {document_id} with context size {context_size}")
            self.processing_progress.emit(document_id, 0)
            
            # Run create_kv_cache.sh
            process = run_script(
                cmd, 
                progress_callback=lambda p: self.processing_progress.emit(document_id, p)
            )
            
            # Check result
            if process.returncode != 0:
                error_message = f"KV cache creation failed with code {process.returncode}"
                if process.stderr:
                    error_message += f": {process.stderr}"
                    
                logging.error(error_message)
                self.processing_complete.emit(document_id, False, error_message)
                return
            
            # Update document registry
            doc_info = {
                'document_id': document_id,
                'file_path': str(temp_file),
                'kv_cache_path': str(kv_cache_path),
                'token_count': token_count,
                'context_size': context_size,
                'model_id': self.config.get('CURRENT_MODEL_ID', 'gemma-3-4b-128k'),
                'created_at': time.time(),
                'last_used': None,
                'usage_count': 0
            }
            
            self._document_registry[document_id] = doc_info
            self._save_document_registry()
            
            # Set as master if requested
            if set_as_master:
                self.set_as_master(document_id)
            
            # Register with cache manager
            self.cache_manager.register_cache(document_id, str(kv_cache_path), context_size)
            
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()
            
            # Notify completion
            self.processing_complete.emit(
                document_id, True, f"KV cache created successfully at {kv_cache_path}"
            )
            
        except Exception as e:
            logging.error(f"Error in document processing thread: {str(e)}")
            self.processing_complete.emit(document_id, False, f"Processing error: {str(e)}")
            
            # Clean up temp file if it exists
            if 'temp_file' in locals() and temp_file.exists():
                temp_file.unlink()
    
    def set_as_master(self, document_id: str) -> bool:
        """Set a document as the master KV cache"""
        if document_id not in self._document_registry:
            logging.error(f"Document not found in registry: {document_id}")
            return False
            
        doc_info = self._document_registry[document_id]
        kv_cache_path = doc_info.get('kv_cache_path')
        
        if not kv_cache_path or not Path(kv_cache_path).exists():
            logging.error(f"KV cache not found for document: {document_id}")
            return False
            
        # Copy to master_cache.bin
        master_cache_path = self.kv_cache_dir / 'master_cache.bin'
        try:
            shutil.copy2(kv_cache_path, master_cache_path)
            logging.info(f"Set {document_id} as master KV cache at {master_cache_path}")
            
            # Update config
            self.config['MASTER_KV_CACHE'] = str(master_cache_path)
            
            # Update document info
            doc_info['is_master'] = True
            self._document_registry[document_id] = doc_info
            self._save_document_registry()
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to set as master KV cache: {str(e)}")
            return False
    
    def _get_document_id(self, document_path: Path) -> str:
        """Generate a consistent document ID from path"""
        # Use filename without extension
        doc_id = document_path.stem.lower()
        
        # Clean up non-alphanumeric characters
        doc_id = re.sub(r'[^a-z0-9_]', '_', doc_id)
        
        return doc_id
