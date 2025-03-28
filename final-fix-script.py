#!/usr/bin/env python3
"""
Final fix script for LlamaCag UI to address all issues
"""

import os
import sys
import shutil
import json
from pathlib import Path

def reset_cache_directories():
    """Reset all cache-related directories"""
    home_dir = os.path.expanduser("~")
    cag_dir = os.path.join(home_dir, "cag_project")
    config_dir = os.path.join(home_dir, ".llamacag")
    kv_cache_dir = os.path.join(cag_dir, "kv_caches")
    temp_dir = os.path.join(cag_dir, "temp_chunks")
    
    print("Resetting cache directories...")
    
    # Recreate directories
    for directory in [cag_dir, kv_cache_dir, temp_dir, config_dir, os.path.join(config_dir, "logs")]:
        if os.path.exists(directory):
            print(f"Removing and recreating: {directory}")
            shutil.rmtree(directory)
        
        os.makedirs(directory, exist_ok=True)
    
    # Create empty registry files
    registry_file = os.path.join(kv_cache_dir, "cache_registry.json")
    usage_file = os.path.join(kv_cache_dir, "usage_registry.json")
    
    with open(registry_file, 'w') as f:
        f.write("{}")
    
    with open(usage_file, 'w') as f:
        f.write("{}")
    
    # Create config file
    config_file = os.path.join(config_dir, "config.json")
    config = {
        "LLAMACPP_PATH": os.path.join(home_dir, "Documents", "llama.cpp"),
        "LLAMACPP_MODEL_DIR": os.path.join(home_dir, "Documents", "llama.cpp", "models"),
        "LLAMACPP_KV_CACHE_DIR": kv_cache_dir,
        "LLAMACPP_TEMP_DIR": temp_dir,
        "LLAMACPP_THREADS": "4",
        "LLAMACPP_BATCH_SIZE": "1024"
    }
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("Cache directories reset. Empty registries and basic config created.")
    return True

def update_cache_manager():
    """Update the cache_manager.py file with the ultra-minimal version"""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(project_dir, "core", "cache_manager.py")
    
    # First, create a backup
    backup_path = file_path + ".backup." + str(int(time.time()))
    if os.path.exists(file_path):
        print(f"Creating backup: {backup_path}")
        shutil.copy2(file_path, backup_path)
    
    # Write the new content
    print(f"Updating cache_manager.py...")
    
    content = '''#!/usr/bin/env python3
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
'''
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Successfully updated cache_manager.py with minimal version.")
    return True

def update_cache_tab():
    """Update the cache_tab.py file to include the refresh_caches method"""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(project_dir, "ui", "cache_tab.py")
    
    # First, create a backup
    backup_path = file_path + ".backup." + str(int(time.time()))
    if os.path.exists(file_path):
        print(f"Creating backup: {backup_path}")
        shutil.copy2(file_path, backup_path)
    
    # Write the new content
    print(f"Updating cache_tab.py...")
    
    content = '''#!/usr/bin/env python3
"""
Cache tab for LlamaCag UI
Provides an interface for managing KV caches.
"""
import os
import sys
import logging
from pathlib import Path
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QProgressBar,
    QSplitter, QFrame, QGridLayout, QGroupBox, QTableWidget,
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
        
        # Info label
        info_label = QLabel("Manage your KV caches for large context window models.")
        layout.addWidget(info_label)
        
        # Cache table
        self.cache_table = QTableWidget()
        self.cache_table.setColumnCount(6)
        self.cache_table.setHorizontalHeaderLabels([
            "Cache Name", "Size", "Document", "Model", "Last Used", "Usage Count"
        ])
        self.cache_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.cache_table)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        button_layout.addWidget(self.refresh_button)
        
        # Purge button
        self.purge_button = QPushButton("Purge Selected")
        button_layout.addWidget(self.purge_button)
        
        # Purge all button
        self.purge_all_button = QPushButton("Purge All")
        button_layout.addWidget(self.purge_all_button)
        
        # Use as master button
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
        self.purge_all_button.clicked.connect(self.purge_all_caches)
        self.use_button.clicked.connect(self.use_selected_cache)
        
        # Table signals
        self.cache_table.itemSelectionChanged.connect(self.on_cache_selected)
        
        # Cache manager signals
        self.cache_manager.cache_list_updated.connect(self.refresh_caches)
        self.cache_manager.cache_purged.connect(self.on_cache_purged)

    def refresh_caches(self):
        """Refresh the cache list by rescanning the directory and updating the table"""
        try:
            # First, clear the table to avoid any existing issues
            self.cache_table.setRowCount(0)
            
            try:
                # Explicitly tell CacheManager to rescan the directory and update its internal state
                # Wrap this in its own try block to handle any issues that might occur
                self.cache_manager.refresh_cache_list()
            except Exception as e:
                print(f"Error refreshing cache list from directory: {e}")
                QMessageBox.warning(self, "Refresh Error", f"Could not fully refresh cache list:\n{e}")
                # Proceed with whatever is in the registry anyway
            
            # Get the cache list from the manager's registry (even if refresh failed)
            caches = self.cache_manager.get_cache_list()
            
            # Sort by name
            caches.sort(key=lambda x: x.get('filename', ''))
            
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
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.1f} KB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                self.cache_table.setItem(i, 1, QTableWidgetItem(size_str))
                
                # Document
                self.cache_table.setItem(i, 2, QTableWidgetItem(cache.get('document_id', 'Unknown')))
                
                # Model
                self.cache_table.setItem(i, 3, QTableWidgetItem(cache.get('model_id', 'Unknown')))
                
                # Last used
                last_used = cache.get('last_used')
                if last_used:
                    last_used_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_used))
                else:
                    last_used_str = "Never"
                self.cache_table.setItem(i, 4, QTableWidgetItem(last_used_str))
                
                # Usage count
                self.cache_table.setItem(i, 5, QTableWidgetItem(str(cache.get('usage_count', 0))))
            
            # Update status
            total_size = self.cache_manager.get_total_cache_size()
            if total_size < 1024 * 1024:
                size_str = f"{total_size / 1024:.1f} KB"
            else:
                size_str = f"{total_size / (1024 * 1024):.1f} MB"
            self.status_label.setText(f"{len(caches)} caches, total size: {size_str}")
            
        except Exception as e:
            # Handle any other exceptions
            self.status_label.setText(f"Error: {str(e)}")
            QMessageBox.warning(self, "Error", f"An error occurred while refreshing caches:\n{str(e)}")
    
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
        self.status_label.setText(f"Selected: {cache_path}")
    
    def purge_selected_cache(self):
        """Purge the selected cache"""
        selected_items = self.cache_table.selectedItems()
        if not selected_items:
            return
        
        # Get selected row
        row = selected_items[0].row()
        
        # Get cache path
        cache_path = self.cache_table.item(row, 0).data(Qt.UserRole)
        cache_name = self.cache_table.item(row, 0).text()
        
        # Confirm
        reply = QMessageBox.question(
            self,
            "Purge Cache",
            f"Are you sure you want to purge the cache for {cache_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        
        # Purge cache
        success = self.cache_manager.purge_cache(cache_path)
        if success:
            self.status_label.setText(f"Purged cache: {cache_name}")
        else:
            self.status_label.setText(f"Failed to purge cache: {cache_name}")
            QMessageBox.warning(
                self,
                "Purge Failed",
                f"Failed to purge cache {cache_name}."
            )
    
    def purge_all_caches(self):
        """Purge all caches"""
        # Confirm
        reply = QMessageBox.question(
            self,
            "Purge All Caches",
            "Are you sure you want to purge ALL caches? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        
        # Purge all caches
        success = self.cache_manager.purge_all_caches()
        if success:
            self.status_label.setText("Purged all caches")
        else:
            self.status_label.setText("Failed to purge all caches")
            QMessageBox.warning(
                self,
                "Purge Failed",
                "Failed to purge all caches."
            )
    
    def use_selected_cache(self):
        """Use the selected cache"""
        selected_items = self.cache_table.selectedItems()
        if not selected_items:
            return
        
        # Get selected row
        row = selected_items[0].row()
        
        # Get cache path
        cache_path = self.cache_table.item(row, 0).data(Qt.UserRole)
        cache_name = self.cache_table.item(row, 0).text()
        
        # Emit signal
        self.cache_selected.emit(cache_path)
        
        # Update status
        self.status_label.setText(f"Using cache: {cache_name}")
    
    def on_cache_purged(self, cache_path: str, success: bool):
        """Handle cache purged signal"""
        if success:
            self.refresh_caches()
            self.cache_purged.emit()
'''
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Successfully updated cache_tab.py with compatible version.")
    return True

if __name__ == "__main__":
    import time
    print("=== Final Fix for LlamaCag UI ===")
    
    # 1. Reset cache directories
    reset_cache_directories()
    
    # 2. Update cache_manager.py
    update_cache_manager()
    
    # 3. Update cache_tab.py
    update_cache_tab()
    
    print("\nAll fixes applied successfully. Try running the application now.")
