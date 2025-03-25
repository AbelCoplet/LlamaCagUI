#!/usr/bin/env python3
"""
KV cache management for LlamaCag UI
Manages KV caches for large context window models.
"""
import os
import sys
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal
class CacheManager(QObject):
    """Manages KV caches for large context window models"""
    # Signals
    cache_list_updated = pyqtSignal()
    cache_purged = pyqtSignal(str, bool)  # cache_path, success
    def __init__(self, config):
        """Initialize cache manager"""
        super().__init__()
        self.config = config
        self.kv_cache_dir = Path(os.path.expanduser(config.get('LLAMACPP_KV_CACHE_DIR', '~/cag_project/kv_caches')))
        # Ensure directory exists
        self.kv_cache_dir.mkdir(parents=True, exist_ok=True)
        # Cache registry
        self._cache_registry = {}
        self._usage_registry = {}
        # Load cache registry
        self._load_cache_registry()
    def _load_cache_registry(self):
        """Load cache registry from disk"""
        registry_file = self.kv_cache_dir / 'cache_registry.json'
        if registry_file.exists():
            try:
                with open(registry_file, 'r') as f:
                    self._cache_registry = json.load(f)
                logging.info(f"Loaded cache registry with {len(self._cache_registry)} entries")
            except Exception as e:
                logging.error(f"Failed to load cache registry: {str(e)}")
        # Load usage registry
        usage_file = self.kv_cache_dir / 'usage_registry.json'
        if usage_file.exists():
            try:
                with open(usage_file, 'r') as f:
                    self._usage_registry = json.load(f)
                logging.info(f"Loaded usage registry with {len(self._usage_registry)} entries")
            except Exception as e:
                logging.error(f"Failed to load usage registry: {str(e)}")
    def _save_cache_registry(self):
        """Save cache registry to disk"""
        registry_file = self.kv_cache_dir / 'cache_registry.json'
        try:
            with open(registry_file, 'w') as f:
                json.dump(self._cache_registry, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save cache registry: {str(e)}")
        # Save usage registry
        usage_file = self.kv_cache_dir / 'usage_registry.json'
        try:
            with open(usage_file, 'w') as f:
                json.dump(self._usage_registry, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save usage registry: {str(e)}")
    def get_cache_list(self) -> List[Dict]:
        """Get list of available KV caches"""
        cache_list = []
        # Get all .bin files in the cache directory
        for file_path in self.kv_cache_dir.glob('**/*.bin'):
            # Skip if hidden
            if file_path.name.startswith('.'):
                continue
            # Get cache ID
            cache_id = file_path.stem
            # Get registry info if available
            registry_info = self._cache_registry.get(str(file_path), {})
            usage_info = self._usage_registry.get(str(file_path), {})
            # Basic info
            cache_info = {
                'id': cache_id,
                'path': str(file_path),
                'filename': file_path.name,
                'size': file_path.stat().st_size,
                'last_modified': file_path.stat().st_mtime,
                'document_id': registry_info.get('document_id', cache_id),
                'document_path': registry_info.get('document_path', ''),
                'context_size': registry_info.get('context_size', 0),
                'token_count': registry_info.get('token_count', 0),
                'model_id': registry_info.get('model_id', ''),
                'last_used': usage_info.get('last_used', None),
                'usage_count': usage_info.get('usage_count', 0)
            }
            cache_list.append(cache_info)
        return cache_list
    def get_cache_info(self, cache_path: str) -> Optional[Dict]:
        """Get detailed information about a KV cache"""
        # Get path object
        path_obj = Path(cache_path)
        if not path_obj.exists():
            return None
        # Get cache ID
        cache_id = path_obj.stem
        # Get registry info if available
        registry_info = self._cache_registry.get(str(path_obj), {})
        usage_info = self._usage_registry.get(str(path_obj), {})
        # Basic info
        cache_info = {
            'id': cache_id,
            'path': str(path_obj),
            'filename': path_obj.name,
            'size': path_obj.stat().st_size,
            'last_modified': path_obj.stat().st_mtime,
            'document_id': registry_info.get('document_id', cache_id),
            'document_path': registry_info.get('document_path', ''),
            'context_size': registry_info.get('context_size', 0),
            'token_count': registry_info.get('token_count', 0),
            'model_id': registry_info.get('model_id', ''),
            'last_used': usage_info.get('last_used', None),
            'usage_count': usage_info.get('usage_count', 0)
        }
        return cache_info
    def register_cache(self, document_id: str, cache_path: str, context_size: int = 0) -> bool:
        """Register a KV cache in the registry"""
        # Validate path
        path_obj = Path(cache_path)
        if not path_obj.exists():
            logging.error(f"Cannot register non-existent cache: {cache_path}")
            return False
        # Update registry
        self._cache_registry[str(path_obj)] = {
            'document_id': document_id,
            'document_path': '',  # Set by document processor
            'context_size': context_size,
            'token_count': 0,  # Set by document processor
            'model_id': self.config.get('CURRENT_MODEL_ID', ''),
            'created_at': time.time()
        }
        # Save registry
        self._save_cache_registry()
        # Emit signal
        self.cache_list_updated.emit()
        return True
    def update_usage(self, cache_path: str) -> bool:
        """Update usage statistics for a KV cache"""
        # Validate path
        path_obj = Path(cache_path)
        if not path_obj.exists():
            logging.error(f"Cannot update usage for non-existent cache: {cache_path}")
            return False
        # Update usage registry
        usage_info = self._usage_registry.get(str(path_obj), {'usage_count': 0})
        usage_info['last_used'] = time.time()
        usage_info['usage_count'] = usage_info.get('usage_count', 0) + 1
        self._usage_registry[str(path_obj)] = usage_info
        # Save registry
        self._save_cache_registry()
        # Emit signal
        self.cache_list_updated.emit()
        return True
    def purge_cache(self, cache_path: str) -> bool:
        """Purge a KV cache"""
        # Validate path
        path_obj = Path(cache_path)
        if not path_obj.exists():
            logging.error(f"Cannot purge non-existent cache: {cache_path}")
            return False
        try:
            # Remove file
            path_obj.unlink()
            # Remove from registries
            if str(path_obj) in self._cache_registry:
                del self._cache_registry[str(path_obj)]
            if str(path_obj) in self._usage_registry:
                del self._usage_registry[str(path_obj)]
            # Save registries
            self._save_cache_registry()
            # Emit signal
            self.cache_purged.emit(str(path_obj), True)
            self.cache_list_updated.emit()
            return True
        except Exception as e:
            logging.error(f"Failed to purge cache {cache_path}: {str(e)}")
            self.cache_purged.emit(str(path_obj), False)
            return False
    def purge_all_caches(self) -> bool:
        """Purge all KV caches"""
        try:
            # Get all cache files
            cache_files = list(self.kv_cache_dir.glob('**/*.bin'))
            # Remove each file
            for path_obj in cache_files:
                # Skip if hidden
                if path_obj.name.startswith('.'):
                    continue
                try:
                    path_obj.unlink()
                except Exception as e:
                    logging.error(f"Failed to remove {path_obj}: {str(e)}")
            # Clear registries
            self._cache_registry = {}
            self._usage_registry = {}
            # Save registries
            self._save_cache_registry()
            # Emit signal
            self.cache_list_updated.emit()
            return True
        except Exception as e:
            logging.error(f"Failed to purge all caches: {str(e)}")
            return False
    def get_total_cache_size(self) -> int:
        """Get the total size of all KV caches in bytes"""
        total_size = 0
        # Get all cache files
        cache_files = list(self.kv_cache_dir.glob('**/*.bin'))
        # Add up sizes
        for path_obj in cache_files:
            # Skip if hidden
            if path_obj.name.startswith('.'):
                continue
            total_size += path_obj.stat().st_size
        return total_size
    def check_cache_compatibility(self, context_size: int) -> List[str]:
        """Check which caches might not be compatible with the given context size"""
        incompatible_caches = []
        # Get all cache info
        cache_list = self.get_cache_list()
        # Check each cache's context size
        for cache_info in cache_list:
            cache_context_size = cache_info.get('context_size', 0)
            # If cache context size is larger than model's, it's incompatible
            if cache_context_size > context_size:
                incompatible_caches.append(cache_info['path'])
        return incompatible_caches
    def update_config(self, config):
        """Update configuration"""
        self.config = config
        new_kv_cache_dir = Path(os.path.expanduser(config.get('LLAMACPP_KV_CACHE_DIR', '~/cag_project/kv_caches')))
        # If directory changed, reload registry
        if new_kv_cache_dir != self.kv_cache_dir:
            self.kv_cache_dir = new_kv_cache_dir
            self.kv_cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_cache_registry()