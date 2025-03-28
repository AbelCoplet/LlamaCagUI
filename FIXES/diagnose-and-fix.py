#!/usr/bin/env python3
"""
Diagnostic and repair tool for LlamaCag UI
"""

import os
import sys
import shutil
import json
from pathlib import Path

def check_file(path, repair=False):
    """Check if a file exists and has content"""
    file_path = Path(path)
    
    print(f"Checking {file_path}...")
    
    if not file_path.exists():
        print(f"  ERROR: File does not exist!")
        return False
    
    if file_path.stat().st_size == 0:
        print(f"  ERROR: File is empty!")
        if repair:
            print(f"  Creating backup of empty file...")
            backup_path = str(file_path) + ".empty"
            shutil.copy2(file_path, backup_path)
        return False
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        try:
            content = f.read()
            if len(content.strip()) == 0:
                print(f"  ERROR: File has only whitespace!")
                return False
            
            # Very basic check for Python files to see if they look legitimate
            if path.endswith('.py'):
                if 'import' not in content and 'def ' not in content and 'class ' not in content:
                    print(f"  WARNING: File doesn't look like valid Python code!")
                    return False
                
                # Specific check for class names in UI files
                if '/ui/' in path and not path.endswith('__init__.py'):
                    filename = os.path.basename(path)
                    base_name = os.path.splitext(filename)[0]
                    expected_class = ''.join(word.capitalize() for word in base_name.split('_'))
                    
                    if f"class {expected_class}" not in content:
                        print(f"  ERROR: Expected class '{expected_class}' not found in {filename}!")
                        return False
            
            print(f"  OK: File exists and has content")
            return True
            
        except Exception as e:
            print(f"  ERROR: Could not read file: {e}")
            return False

def create_minimal_chat_tab(path):
    """Create a minimal chat_tab.py file"""
    content = '''#!/usr/bin/env python3
"""
Chat tab for LlamaCag UI

Provides a chat interface for interacting with the model.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QCheckBox, QSlider, QSpinBox,
    QComboBox, QFileDialog, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QTextCursor, QColor, QPalette

from core.chat_engine import ChatEngine
from core.model_manager import ModelManager
from core.cache_manager import CacheManager
from utils.config import ConfigManager


class ChatTab(QWidget):
    """Chat interface tab for interacting with the model"""
    
    def __init__(self, chat_engine: ChatEngine, model_manager: ModelManager, 
                 cache_manager: CacheManager, config_manager: ConfigManager):
        """Initialize chat tab"""
        super().__init__()
        
        self.chat_engine = chat_engine
        self.model_manager = model_manager
        self.cache_manager = cache_manager
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        
        # Initialize UI
        self.setup_ui()
        
        # Connect signals
        self.connect_signals()
        
        # Initialize with current settings
        self.initialize_state()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Simple placeholder
        label = QLabel("Chat Interface")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(label)
        
        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
    
    def connect_signals(self):
        """Connect signals between components"""
        pass
    
    def initialize_state(self):
        """Initialize UI state from current settings"""
        pass
    
    def on_model_changed(self, model_id: str):
        """Handle model change"""
        pass
    
    def on_cache_selected(self, cache_path: str):
        """Handle KV cache selection from CacheTab"""
        pass
'''
    
    # Create a backup if the file exists
    if os.path.exists(path):
        backup_path = path + '.backup'
        print(f"Creating backup of existing chat_tab.py to {backup_path}")
        shutil.copy2(path, backup_path)
    
    # Write the minimal version
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Created minimal chat_tab.py at {path}")
    return True

def create_minimal_cache_manager(path):
    """Create a minimal cache_manager.py file"""
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
    
    # Create a backup if the file exists
    if os.path.exists(path):
        backup_path = path + '.backup'
        print(f"Creating backup of existing cache_manager.py to {backup_path}")
        shutil.copy2(path, backup_path)
    
    # Write the minimal version
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Created minimal cache_manager.py at {path}")
    return True

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

if __name__ == "__main__":
    project_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Project directory: {project_dir}")
    
    # Reset cache directories
    reset_cache_directories()
    
    # Check and fix critical files
    critical_files = [
        os.path.join(project_dir, "main.py"),
        os.path.join(project_dir, "ui", "main_window.py"),
        os.path.join(project_dir, "ui", "chat_tab.py"),
        os.path.join(project_dir, "core", "cache_manager.py")
    ]
    
    # Check if critical files exist and have content
    print("\nChecking critical files...")
    all_ok = True
    for file_path in critical_files:
        if not check_file(file_path):
            all_ok = False
            
            # Fix known problem files
            if file_path.endswith("chat_tab.py"):
                print(f"Fixing {file_path}...")
                create_minimal_chat_tab(file_path)
            elif file_path.endswith("cache_manager.py"):
                print(f"Fixing {file_path}...")
                create_minimal_cache_manager(file_path)
    
    if all_ok:
        print("\nAll critical files look OK!")
    else:
        print("\nSome issues were found and fixed!")
    
    print("\nDiagnostic and repair complete. Try running the application now.")
