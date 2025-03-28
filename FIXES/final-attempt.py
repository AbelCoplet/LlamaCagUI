#!/usr/bin/env python3
"""
Final attempt to fix all issues in LlamaCag UI
"""
import os
import shutil

def reset_cache():
    """Reset cache directories"""
    print("Resetting cache directories...")
    
    # Reset cache directories
    home = os.path.expanduser("~")
    for dir_path in [
        os.path.join(home, "cag_project"),
        os.path.join(home, ".llamacag")
    ]:
        if os.path.exists(dir_path):
            print(f"Removing directory: {dir_path}")
            shutil.rmtree(dir_path)
    
    # Create basic structure
    for dir_path in [
        os.path.join(home, "cag_project", "kv_caches"),
        os.path.join(home, "cag_project", "temp_chunks"),
        os.path.join(home, ".llamacag", "logs")
    ]:
        os.makedirs(dir_path, exist_ok=True)
    
    # Create empty registry files
    for file_path in [
        os.path.join(home, "cag_project", "kv_caches", "cache_registry.json"),
        os.path.join(home, "cag_project", "kv_caches", "usage_registry.json")
    ]:
        with open(file_path, 'w') as f:
            f.write("{}")
    
    # Create config file
    config_path = os.path.join(home, ".llamacag", "config.json")
    with open(config_path, 'w') as f:
        f.write('''{
  "LLAMACPP_PATH": "~/Documents/llama.cpp",
  "LLAMACPP_MODEL_DIR": "~/Documents/llama.cpp/models",
  "LLAMACPP_KV_CACHE_DIR": "~/cag_project/kv_caches",
  "LLAMACPP_TEMP_DIR": "~/cag_project/temp_chunks",
  "LLAMACPP_THREADS": "4",
  "LLAMACPP_BATCH_SIZE": "1024"
}''')
    
    print("Cache directories and files reset.")

def fix_cache_tab():
    """Replace cache_tab.py with simplest version"""
    file_path = os.path.join(os.path.dirname(__file__), "ui", "cache_tab.py")
    backup_path = file_path + ".final_backup"
    
    # Create backup
    if os.path.exists(file_path):
        print(f"Creating backup: {backup_path}")
        shutil.copy2(file_path, backup_path)
    
    # Write simplified version
    print(f"Writing simplified cache_tab.py...")
    with open(file_path, 'w') as f:
        f.write('''#!/usr/bin/env python3
"""
Simplest possible cache_tab.py for LlamaCag UI
"""
import os
import sys
import time
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal
from core.cache_manager import CacheManager
from core.document_processor import DocumentProcessor
from utils.config import ConfigManager

class CacheTab(QWidget):
    """KV cache management tab"""
    # Signals
    cache_selected = pyqtSignal(str)  # cache_path
    cache_purged = pyqtSignal()
    
    def __init__(self, cache_manager: CacheManager, document_processor: DocumentProcessor,
                 config_manager: ConfigManager):
        """Initialize cache tab"""
        super().__init__()
        self.cache_manager = cache_manager
        self.document_processor = document_processor
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        
        # Set up UI
        self.setup_ui()
        
        # Connect signals
        self.connect_signals()
        
        # Load caches
        self.refresh_caches()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Header label
        header = QLabel("KV Cache Management")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        # Cache table
        self.cache_table = QTableWidget()
        self.cache_table.setColumnCount(3)
        self.cache_table.setHorizontalHeaderLabels([
            "Cache Name", "Size", "Document"
        ])
        layout.addWidget(self.cache_table)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        button_layout.addWidget(self.refresh_button)
        
        # Purge button
        self.purge_button = QPushButton("Purge Selected")
        button_layout.addWidget(self.purge_button)
        
        # Use button
        self.use_button = QPushButton("Use Selected")
        button_layout.addWidget(self.use_button)
        
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
    
    def connect_signals(self):
        """Connect signals between components"""
        # Button signals
        self.refresh_button.clicked.connect(self.refresh_caches)
        self.purge_button.clicked.connect(self.purge_selected_cache)
        self.use_button.clicked.connect(self.use_selected_cache)
        
        # Table signals
        self.cache_table.itemSelectionChanged.connect(self.on_cache_selected)
        
        # Cache manager signals
        self.cache_manager.cache_list_updated.connect(self.refresh_caches)
        self.cache_manager.cache_purged.connect(self.on_cache_purged)

    def refresh_caches(self):
        """Refresh the cache list"""
        try:
            # Clear the table
            self.cache_table.setRowCount(0)
            
            # Refresh cache list in manager
            try:
                self.cache_manager.refresh_cache_list()
            except Exception as e:
                QMessageBox.warning(self, "Refresh Error", "Could not refresh cache list")
            
            # Get the cache list
            caches = self.cache_manager.get_cache_list()
            
            # Add to table
            for i, cache in enumerate(caches):
                self.cache_table.insertRow(i)
                
                # Cache name
                item = QTableWidgetItem(cache.get('filename', 'Unknown'))
                item.setData(Qt.UserRole, cache.get('path', ''))
                self.cache_table.setItem(i, 0, item)
                
                # Size
                size_bytes = cache.get('size', 0)
                if size_bytes < 1024:
                    size_str = str(size_bytes) + " B"
                elif size_bytes < 1024 * 1024:
                    size_str = str(int(size_bytes / 1024)) + " KB"
                else:
                    size_str = str(int(size_bytes / (1024 * 1024))) + " MB"
                self.cache_table.setItem(i, 1, QTableWidgetItem(size_str))
                
                # Document
                self.cache_table.setItem(i, 2, QTableWidgetItem(cache.get('document_id', 'Unknown')))
            
            # Update status
            self.status_label.setText(str(len(caches)) + " caches")
            
        except Exception as e:
            self.status_label.setText("Error refreshing caches")
    
    def on_cache_selected(self):
        """Handle cache selection change"""
        selected_items = self.cache_table.selectedItems()
        if not selected_items:
            return
        
        # Get selected row
        row = selected_items[0].row()
        
        # Get cache path
        cache_path = self.cache_table.item(row, 0).data(Qt.UserRole)
        
        # Update status
        self.status_label.setText("Selected: " + str(cache_path))
    
    def purge_selected_cache(self):
        """Purge the selected cache"""
        selected_items = self.cache_table.selectedItems()
        if not selected_items:
            return
        
        # Get selected row
        row = selected_items[0].row()
        
        # Get cache path
        cache_path = self.cache_table.item(row, 0).data(Qt.UserRole)
        
        # Purge cache
        success = self.cache_manager.purge_cache(cache_path)
        if success:
            self.status_label.setText("Cache purged")
        else:
            self.status_label.setText("Failed to purge cache")
    
    def use_selected_cache(self):
        """Use the selected cache"""
        selected_items = self.cache_table.selectedItems()
        if not selected_items:
            return
        
        # Get selected row
        row = selected_items[0].row()
        
        # Get cache path
        cache_path = self.cache_table.item(row, 0).data(Qt.UserRole)
        
        # Emit signal
        self.cache_selected.emit(cache_path)
        
        # Update status
        self.status_label.setText("Using selected cache")
    
    def on_cache_purged(self, cache_path, success):
        """Handle cache purged signal"""
        if success:
            self.refresh_caches()
            self.cache_purged.emit()
''')
    
    print("cache_tab.py updated with simplified version.")

def fix_cache_manager():
    """Replace cache_manager.py with ultra-minimal version"""
    file_path = os.path.join(os.path.dirname(__file__), "core", "cache_manager.py")
    backup_path = file_path + ".final_backup"
    
    # Create backup
    if os.path.exists(file_path):
        print(f"Creating backup: {backup_path}")
        shutil.copy2(file_path, backup_path)
    
    # Write ultra-minimal version
    print(f"Writing ultra-minimal cache_manager.py...")
    with open(file_path, 'w') as f:
        f.write('''#!/usr/bin/env python3
"""
Ultra minimal KV cache management for LlamaCag UI
A simplified version that avoids any recursion risk
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from PyQt5.QtCore import QObject, pyqtSignal

class CacheManager(QObject):
    """Minimal manager for KV caches with no directory traversal"""
    # Signals
    cache_list_updated = pyqtSignal()
    cache_purged = pyqtSignal(str, bool)  # cache_path, success

    def __init__(self, config):
        """Initialize cache manager"""
        super().__init__()
        self.config = config
        
        # Use a simple string path to avoid any Path object issues
        cache_dir = config.get('LLAMACPP_KV_CACHE_DIR', '')
        if not cache_dir:
            cache_dir = os.path.join(os.path.expanduser('~'), 'cag_project', 'kv_caches')
        self.kv_cache_dir = os.path.expanduser(cache_dir)
        
        # Create directory if it doesn't exist
        if not os.path.exists(self.kv_cache_dir):
            os.makedirs(self.kv_cache_dir, exist_ok=True)
        
        # Registry paths
        self.registry_path = os.path.join(self.kv_cache_dir, 'cache_registry.json')
        self.usage_path = os.path.join(self.kv_cache_dir, 'usage_registry.json')
        
        # Create empty registry files if they don't exist
        if not os.path.exists(self.registry_path):
            with open(self.registry_path, 'w') as f:
                f.write("{}")
        if not os.path.exists(self.usage_path):
            with open(self.usage_path, 'w') as f:
                f.write("{}")
        
        # Load registries
        self._cache_registry = self._load_json(self.registry_path, {})
        self._usage_registry = self._load_json(self.usage_path, {})
    
    def _load_json(self, path, default=None):
        """Safe JSON loading with fallback"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load {path}: {e}")
            return default if default is not None else {}
    
    def _save_json(self, path, data):
        """Safe JSON saving"""
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save {path}: {e}")
            return False
    
    def refresh_cache_list(self):
        """Update registry by checking files - NO DIRECTORY SCANNING"""
        print("Checking registry entries (NO DIRECTORY SCANNING)")
        
        # Remove entries for non-existent files
        for path in list(self._cache_registry.keys()):
            if not os.path.exists(path):
                del self._cache_registry[path]
                if path in self._usage_registry:
                    del self._usage_registry[path]
        
        # Save updated registry
        self._save_json(self.registry_path, self._cache_registry)
        self._save_json(self.usage_path, self._usage_registry)
        
        # Notify UI
        self.cache_list_updated.emit()
    
    def get_cache_list(self) -> List[Dict]:
        """Get list of available KV caches"""
        result = []
        
        for path, info in self._cache_registry.items():
            # Skip non-existent files
            if not os.path.exists(path):
                continue
            
            try:
                # Get basic file stats
                stat = os.stat(path)
                filename = os.path.basename(path)
                
                # Get usage info
                usage = self._usage_registry.get(path, {})
                
                # Create cache info
                cache_info = {
                    'id': info.get('document_id', filename),
                    'path': path,
                    'filename': filename,
                    'size': stat.st_size,
                    'last_modified': stat.st_mtime,
                    'document_id': info.get('document_id', os.path.splitext(filename)[0]),
                    'original_file_path': info.get('original_file_path', ''),
                    'context_size': info.get('context_size', 0),
                    'token_count': info.get('token_count', 0),
                    'model_id': info.get('model_id', ''),
                    'created_at': info.get('created_at', None),
                    'last_used': usage.get('last_used', None),
                    'usage_count': usage.get('usage_count', 0),
                    'is_master': info.get('is_master', False)
                }
                
                result.append(cache_info)
            except Exception as e:
                print(f"Error getting info for {path}: {e}")
        
        # Sort by last used time
        result.sort(key=lambda x: x.get('last_used') or x.get('created_at') or 0, reverse=True)
        return result
    
    def get_cache_info(self, cache_path: str) -> Optional[Dict]:
        """Get detailed information about a KV cache"""
        if not cache_path or not os.path.exists(cache_path):
            return None
        
        if cache_path not in self._cache_registry:
            return None
        
        try:
            # Get basic file stats
            stat = os.stat(cache_path)
            filename = os.path.basename(cache_path)
            
            # Get registry info
            info = self._cache_registry.get(cache_path, {})
            usage = self._usage_registry.get(cache_path, {})
            
            # Create cache info
            cache_info = {
                'id': info.get('document_id', filename),
                'path': cache_path,
                'filename': filename,
                'size': stat.st_size,
                'last_modified': stat.st_mtime,
                'document_id': info.get('document_id', os.path.splitext(filename)[0]),
                'original_file_path': info.get('original_file_path', ''),
                'context_size': info.get('context_size', 0),
                'token_count': info.get('token_count', 0),
                'model_id': info.get('model_id', ''),
                'created_at': info.get('created_at', None),
                'last_used': usage.get('last_used', None),
                'usage_count': usage.get('usage_count', 0),
                'is_master': info.get('is_master', False)
            }
            
            return cache_info
        except Exception as e:
            print(f"Error getting info for {cache_path}: {e}")
            return None
    
    def register_cache(self, document_id: str, cache_path: str, context_size: int,
                       token_count: int = 0, original_file_path: str = "", model_id: str = "", 
                       is_master: bool = False) -> bool:
        """Register a KV cache in the registry"""
        if not cache_path or not os.path.exists(cache_path):
            print(f"Cannot register non-existent cache: {cache_path}")
            return False
        
        self._cache_registry[cache_path] = {
            'document_id': document_id,
            'original_file_path': original_file_path,
            'context_size': context_size,
            'token_count': token_count,
            'model_id': model_id,
            'created_at': time.time(),
            'is_master': is_master
        }
        
        if cache_path not in self._usage_registry:
            self._usage_registry[cache_path] = {'last_used': None, 'usage_count': 0}
        
        # Save changes
        self._save_json(self.registry_path, self._cache_registry)
        self._save_json(self.usage_path, self._usage_registry)
        
        # Notify UI
        self.cache_list_updated.emit()
        return True
    
    def update_usage_by_path(self, cache_path: str) -> bool:
        """Update usage statistics for a KV cache"""
        if not cache_path or not os.path.exists(cache_path):
            return False
        
        if cache_path not in self._cache_registry:
            return False
        
        # Update usage
        usage = self._usage_registry.get(cache_path, {'usage_count': 0})
        usage['last_used'] = time.time()
        usage['usage_count'] = usage.get('usage_count', 0) + 1
        self._usage_registry[cache_path] = usage
        
        # Save changes
        self._save_json(self.usage_path, self._usage_registry)
        
        # Notify UI
        self.cache_list_updated.emit()
        return True
    
    def purge_cache(self, cache_path: str) -> bool:
        """Purge a KV cache file and its registry entries"""
        if not cache_path:
            return False
        
        file_existed = os.path.exists(cache_path)
        
        # Try to delete the file
        if file_existed:
            try:
                os.remove(cache_path)
                print(f"Deleted cache file: {cache_path}")
            except Exception as e:
                print(f"Failed to delete {cache_path}: {e}")
                return False
        
        # Remove from registries
        if cache_path in self._cache_registry:
            del self._cache_registry[cache_path]
        if cache_path in self._usage_registry:
            del self._usage_registry[cache_path]
        
        # Save changes
        self._save_json(self.registry_path, self._cache_registry)
        self._save_json(self.usage_path, self._usage_registry)
        
        # Notify UI
        self.cache_purged.emit(cache_path, True)
        self.cache_list_updated.emit()
        return True
    
    def purge_all_caches(self) -> bool:
        """Purge all KV cache files and clear registries"""
        success = True
        
        # Delete each file
        for path in list(self._cache_registry.keys()):
            if os.path.exists(path):
                try:
                    os.remove(path)
                    print(f"Deleted cache file: {path}")
                except Exception as e:
                    print(f"Failed to delete {path}: {e}")
                    success = False
        
        # Clear registries
        self._cache_registry = {}
        self._usage_registry = {}
        
        # Save empty registries
        self._save_json(self.registry_path, self._cache_registry)
        self._save_json(self.usage_path, self._usage_registry)
        
        # Notify UI
        self.cache_list_updated.emit()
        return success
    
    def get_total_cache_size(self) -> int:
        """Get the total size of all registered KV caches in bytes"""
        total_size = 0
        
        for path in self._cache_registry.keys():
            if os.path.exists(path):
                try:
                    total_size += os.path.getsize(path)
                except Exception as e:
                    print(f"Failed to get size of {path}: {e}")
        
        return total_size
    
    def check_cache_compatibility(self, model_context_size: int) -> List[str]:
        """Check which caches might be incompatible with the given model context size"""
        incompatible = []
        
        for path, info in self._cache_registry.items():
            if os.path.exists(path):
                cache_context = info.get('context_size', 0)
                if cache_context > model_context_size:
                    incompatible.append(path)
        
        return incompatible
    
    def update_config(self, config):
        """Update configuration and reload registries if path changed"""
        old_dir = self.kv_cache_dir
        
        # Get new cache directory
        cache_dir = config.get('LLAMACPP_KV_CACHE_DIR', '')
        if not cache_dir:
            cache_dir = os.path.join(os.path.expanduser('~'), 'cag_project', 'kv_caches')
        new_dir = os.path.expanduser(cache_dir)
        
        # Update config
        self.config = config
        
        # Check if directory changed
        if new_dir != old_dir:
            print(f"KV cache directory changed: {old_dir} -> {new_dir}")
            self.kv_cache_dir = new_dir
            
            # Create directory if needed
            if not os.path.exists(self.kv_cache_dir):
                os.makedirs(self.kv_cache_dir, exist_ok=True)
            
            # Update registry paths
            self.registry_path = os.path.join(self.kv_cache_dir, 'cache_registry.json')
            self.usage_path = os.path.join(self.kv_cache_dir, 'usage_registry.json')
            
            # Reload registries
            self._cache_registry = self._load_json(self.registry_path, {})
            self._usage_registry = self._load_json(self.usage_path, {})
            
            # Notify UI
            self.cache_list_updated.emit()
''')
    
    print("cache_manager.py updated with ultra-minimal version.")

if __name__ == "__main__":
    print("=== FINAL ATTEMPT TO FIX LLAMACAG UI ===")
    
    try:
        # Step 1: Reset cache directories
        reset_cache()
        
        # Step 2: Replace cache_tab.py
        fix_cache_tab()
        
        # Step 3: Replace cache_manager.py
        fix_cache_manager()
        
        print("\nFixes applied successfully. Try running the application now.")
        print("If it still doesn't work, please consider reinstalling the application in a new directory.")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        print("Fix attempt failed. Please reinstall the application in a fresh directory.")
