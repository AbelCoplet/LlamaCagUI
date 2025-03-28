#!/usr/bin/env python3
"""
Document tab for LlamaCag UI

Provides an interface for selecting and processing documents into KV caches.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Union

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QPushButton, QLabel, QFileDialog, QProgressBar,
    QListWidget, QListWidgetItem, QCheckBox, QSpinBox,
    QGroupBox, QFrame, QSplitter, QMessageBox, QToolButton,
    QScrollArea
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QFont

import logging # Added logging
from core.document_processor import DocumentProcessor
from core.model_manager import ModelManager
from core.cache_manager import CacheManager # Added CacheManager import
from utils.config import ConfigManager
from utils.token_counter import estimate_tokens_for_file


class DocumentTab(QWidget):
    """Document processing tab for creating KV caches"""
    
    # Signals
    kv_cache_created = pyqtSignal(str, bool)  # cache_path, success
    document_removed = pyqtSignal(str) # Signal when a document is removed

    # Add cache_manager to constructor
    def __init__(self, document_processor: DocumentProcessor, model_manager: ModelManager,
                 cache_manager: CacheManager, config_manager: ConfigManager):
        """Initialize document tab"""
        super().__init__()

        self.document_processor = document_processor
        self.model_manager = model_manager
        self.cache_manager = cache_manager # Store cache_manager
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        
        # Document tracking
        self.selected_documents = []
        self.current_document_path = None
        
        # Initialize UI
        self.setup_ui()
        
        # Connect signals
        self.connect_signals()
        
        # Load document state
        self.load_documents()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Model info panel
        model_frame = QFrame()
        # model_frame.setFrameShape(QFrame.StyledPanel) # Removed shape
        # model_frame.setStyleSheet("background-color: #f5f9ff;") # Removed background
        model_layout = QHBoxLayout(model_frame)
        
        self.model_label = QLabel("Current Model: None")
        # self.model_label.setStyleSheet("color: #000000; font-weight: bold;") # Use default color
        self.model_label.setStyleSheet("font-weight: bold;")
        model_layout.addWidget(self.model_label)
        
        model_layout.addStretch()
        
        self.context_label = QLabel("Context Size: 0 tokens")
        model_layout.addWidget(self.context_label)
        
        layout.addWidget(model_frame)
        
        # Main area splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Document selection
        doc_group = QGroupBox("Document Selection")
        doc_layout = QVBoxLayout(doc_group)
        
        # Document list
        self.document_list = QListWidget()
        self.document_list.setMinimumWidth(300)
        doc_layout.addWidget(self.document_list)
        
        # Document buttons
        doc_buttons = QHBoxLayout()
        
        self.select_file_button = QPushButton("Select File")
        doc_buttons.addWidget(self.select_file_button)
        
        self.select_folder_button = QPushButton("Select Folder")
        doc_buttons.addWidget(self.select_folder_button)

        self.remove_doc_button = QPushButton("Remove Selected") # New remove button
        self.remove_doc_button.setEnabled(False) # Initially disabled
        self.remove_doc_button.setStyleSheet("background-color: #ffcccc;") # Make it look deletish
        doc_buttons.addWidget(self.remove_doc_button)

        self.clear_docs_button = QPushButton("Clear All") # Renamed for clarity
        doc_buttons.addWidget(self.clear_docs_button)

        doc_layout.addLayout(doc_buttons)
        
        splitter.addWidget(doc_group)
        
        # Document info and processing
        processing_group = QGroupBox("Document Processing")
        processing_layout = QVBoxLayout(processing_group)
        
        # Document info
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_layout = QGridLayout(info_frame)
        info_layout.setSpacing(8) # Add some spacing within the grid
        
        info_layout.addWidget(QLabel("Selected Document:"), 0, 0)
        self.doc_name_label = QLabel("None")
        self.doc_name_label.setWordWrap(True) # Allow name to wrap if long
        info_layout.addWidget(self.doc_name_label, 0, 1)
        
        info_layout.addWidget(QLabel("File Size:"), 1, 0)
        self.file_size_label = QLabel("0 KB")
        info_layout.addWidget(self.file_size_label, 1, 1)
        
        info_layout.addWidget(QLabel("Estimated Tokens:"), 2, 0)
        self.token_count_label = QLabel("0")
        info_layout.addWidget(self.token_count_label, 2, 1)
        
        info_layout.addWidget(QLabel("Context Fit:"), 3, 0)
        self.context_fit_label = QLabel("Unknown")
        info_layout.addWidget(self.context_fit_label, 3, 1)
        
        processing_layout.addWidget(info_frame)
        
        # Processing options
        options_frame = QFrame()
        options_layout = QHBoxLayout(options_frame)
        
        self.set_master_checkbox = QCheckBox("Set as Master KV Cache")
        options_layout.addWidget(self.set_master_checkbox)
        
        options_layout.addStretch()
        
        self.estimate_button = QPushButton("Estimate Tokens")
        self.estimate_button.setEnabled(False)
        options_layout.addWidget(self.estimate_button)
        
        self.process_button = QPushButton("Create KV Cache")
        self.process_button.setEnabled(False)
        self.process_button.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; padding: 8px 16px; }"
        )
        options_layout.addWidget(self.process_button)
        
        processing_layout.addWidget(options_frame)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        processing_layout.addWidget(self.progress_bar)
        
        # Status message
        self.status_label = QLabel("Ready")
        processing_layout.addWidget(self.status_label)
        
        # Add stretch at the bottom
        processing_layout.addStretch()
        
        splitter.addWidget(processing_group)
        
        # Set initial splitter sizes - give slightly more to the right panel
        splitter.setSizes([350, 650]) 
        
        layout.addWidget(splitter, 1)
    
    def connect_signals(self):
        """Connect signals between components"""
        # Button signals
        self.select_file_button.clicked.connect(self.select_document_file)
        self.select_folder_button.clicked.connect(self.select_document_folder)
        self.remove_doc_button.clicked.connect(self.remove_selected_document) # Connect remove button
        self.clear_docs_button.clicked.connect(self.clear_all_documents) # Connect renamed clear button
        self.estimate_button.clicked.connect(self.estimate_document_tokens)
        self.process_button.clicked.connect(self.process_document)

        # List signals
        self.document_list.itemSelectionChanged.connect(self.on_document_selected)
        
        # Document processor signals
        self.document_processor.token_estimation_complete.connect(self.on_token_estimation_complete)
        self.document_processor.processing_progress.connect(self.on_processing_progress)
        self.document_processor.processing_complete.connect(self.on_processing_complete)
    
    def load_documents(self):
        """Load saved document paths"""
        doc_paths = self.config.get('RECENT_DOCUMENTS', [])
        if not doc_paths:
            return
        
        for path in doc_paths:
            path_obj = Path(path)
            if path_obj.exists():
                self.add_document_to_list(path_obj)
    
    def add_document_to_list(self, document_path: Path):
        """Add a document to the list"""
        # Check if already in list
        for i in range(self.document_list.count()):
            item = self.document_list.item(i)
            if item.data(Qt.UserRole) == str(document_path):
                return
        
        # Create list item
        item = QListWidgetItem(document_path.name)
        item.setData(Qt.UserRole, str(document_path))
        
        # Add to list
        self.document_list.addItem(item)
        
        # Add to tracking
        self.selected_documents.append(str(document_path))
        
        # Save to config
        self.config['RECENT_DOCUMENTS'] = self.selected_documents
        self.config_manager.save_config()

    # Renamed function
    def clear_all_documents(self):
        """Clear the document selection list entirely."""
        reply = QMessageBox.question(
            self, "Clear All Documents",
            "Are you sure you want to remove all documents from this list?\n(This will NOT delete the files themselves or their caches.)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        self.document_list.clear()
        self.selected_documents = []

        # Update document info
        self.update_document_info(None)

        # Save to config
        self.config['RECENT_DOCUMENTS'] = []
        self.config_manager.save_config()
        self.status_label.setText("Document list cleared.")


    def select_document_file(self):
        """Select a document file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Document", "", 
            "Text Documents (*.txt *.md *.pdf *.html *.docx);;All Files (*)"
        )
        
        if not file_path:
            return
            
        path_obj = Path(file_path)
        self.add_document_to_list(path_obj)
        
        # Select the new item
        for i in range(self.document_list.count()):
            item = self.document_list.item(i)
            if item.data(Qt.UserRole) == str(path_obj):
                self.document_list.setCurrentItem(item)
                break
    
    def select_document_folder(self):
        """Select a folder of documents"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Document Folder", "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if not folder_path:
            return
            
        # Ask if user wants to process all text files in the folder
        reply = QMessageBox.question(
            self, "Process Folder", 
            "Do you want to add all text documents from this folder?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            # Just add the folder itself
            path_obj = Path(folder_path)
            self.add_document_to_list(path_obj)
        else:
            # Add all text files in the folder
            path_obj = Path(folder_path)
            count = 0
            
            for ext in ['.txt', '.md', '.pdf', '.html', '.docx']:
                for file_path in path_obj.glob(f"**/*{ext}"):
                    self.add_document_to_list(file_path)
                    count += 1
            
            if count == 0:
                QMessageBox.information(
                    self, "No Documents Found",
                    "No text documents found in the selected folder."
                )

    def remove_selected_document(self):
        """Remove the selected document entry and its associated KV cache."""
        items = self.document_list.selectedItems()
        if not items:
            return

        item = items[0]
        doc_path_str = item.data(Qt.UserRole)
        doc_path = Path(doc_path_str)
        doc_name = doc_path.name

        reply = QMessageBox.question(
            self, "Remove Document",
            f"Are you sure you want to remove '{doc_name}' from the list and delete its associated KV cache (if found)?\n\n(This will NOT delete the original document file.)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        # Find associated cache
        cache_to_purge = None
        all_caches = self.cache_manager.get_cache_list() # Use self.cache_manager
        for cache_info in all_caches:
            # Compare resolved paths to be safe
            if 'original_document' in cache_info and cache_info['original_document'] != "Unknown":
                 try:
                     original_doc_path = Path(cache_info['original_document'])
                     if original_doc_path.resolve() == doc_path.resolve():
                         cache_to_purge = cache_info['path']
                         break
                 except Exception as e:
                     logging.warning(f"Error resolving path during cache check: {e}")


        # Purge cache if found
        if cache_to_purge:
            logging.info(f"Purging cache {cache_to_purge} associated with document {doc_path_str}")
            if not self.cache_manager.purge_cache(cache_to_purge):
                QMessageBox.warning(self, "Cache Purge Failed", f"Failed to delete the KV cache file:\n{cache_to_purge}")
                # Decide whether to proceed with removing the list item anyway
        else:
            logging.info(f"No associated KV cache found for document {doc_path_str}")

        # Remove from UI list
        row = self.document_list.row(item)
        self.document_list.takeItem(row)

        # Remove from tracking list
        if doc_path_str in self.selected_documents:
            self.selected_documents.remove(doc_path_str)

        # Update config
        self.config['RECENT_DOCUMENTS'] = self.selected_documents
        self.config_manager.save_config()

        # Update UI state (clear info panel if nothing else is selected)
        if not self.document_list.selectedItems():
             # If we just removed the last item, clear the info panel
             if self.document_list.count() == 0:
                 self.update_document_info(None)
             # Otherwise, select the next item if available
             elif row < self.document_list.count():
                 self.document_list.setCurrentRow(row)
             elif self.document_list.count() > 0:
                 self.document_list.setCurrentRow(self.document_list.count() - 1)


        self.status_label.setText(f"Removed document: {doc_name}")
        self.document_removed.emit(doc_path_str) # Emit signal


    def on_document_selected(self):
        """Handle document selection change"""
        items = self.document_list.selectedItems()
        if not items:
            self.update_document_info(None)
            return
            
        # Get path from selected item
        item = items[0]
        document_path = item.data(Qt.UserRole)
        
        # Update document info
        self.update_document_info(Path(document_path))
    
    def update_document_info(self, document_path: Optional[Path]):
        """Update document info display"""
        self.current_document_path = document_path
        
        if not document_path:
            self.doc_name_label.setText("None")
            self.file_size_label.setText("0 KB")
            self.token_count_label.setText("0")
            self.context_fit_label.setText("Unknown")
            self.estimate_button.setEnabled(False)
            self.process_button.setEnabled(False)
            self.remove_doc_button.setEnabled(False) # Disable remove button too
            return

        # Document exists?
        if not document_path.exists():
            self.doc_name_label.setText(f"{document_path.name} (not found)")
            self.file_size_label.setText("N/A")
            self.token_count_label.setText("N/A")
            self.context_fit_label.setText("N/A")
            self.estimate_button.setEnabled(False)
            self.process_button.setEnabled(False)
            self.remove_doc_button.setEnabled(False) # Disable remove button too
            return

        # Update labels
        self.doc_name_label.setText(document_path.name)
        
        # File size
        size_bytes = document_path.stat().st_size
        if size_bytes < 1024:
            size_str = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
            
        self.file_size_label.setText(size_str)
        
        # Enable buttons
        self.estimate_button.setEnabled(True)
        self.process_button.setEnabled(True)
        self.remove_doc_button.setEnabled(True) # Enable remove button

        # Quick token estimate
        quick_estimate = size_bytes // 4  # Rough estimate: 4 bytes per token
        
        # Get model context size
        model_id = self.config.get('CURRENT_MODEL_ID')
        if model_id:
            model_info = self.model_manager.get_model_info(model_id)
            if model_info:
                context_size = model_info.get('context_window', 128000)
                self.context_label.setText(f"Context Size: {context_size:,} tokens")
                
                # Update fit status based on quick estimate
                if quick_estimate > context_size:
                    self.context_fit_label.setText("Too large (estimate)")
                    self.context_fit_label.setStyleSheet("color: #F44336; font-weight: bold;")
                else:
                    self.context_fit_label.setText("Likely fits (estimate)")
                    self.context_fit_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                self.context_label.setText("Context Size: Unknown")
        
        self.token_count_label.setText(f"~{quick_estimate:,} (rough estimate)")
    
    def estimate_document_tokens(self):
        """Estimate tokens for the selected document"""
        if not self.current_document_path or not self.current_document_path.exists():
            return
            
        # Update status
        self.status_label.setText(f"Estimating tokens for {self.current_document_path.name}...")
        
        # Start estimation
        try:
            # For larger files, use the document processor's estimation
            if self.current_document_path.stat().st_size > 1024 * 1024:  # > 1MB
                self.document_processor.estimate_tokens(self.current_document_path)
            else:
                # For smaller files, do it directly
                token_count = estimate_tokens_for_file(self.current_document_path)
                self.on_token_estimation_complete("", token_count, True)
                
        except Exception as e:
            self.status_label.setText(f"Error estimating tokens: {str(e)}")
    
    def process_document(self):
        """Process the selected document"""
        if not self.current_document_path or not self.current_document_path.exists():
            return
            
        # Confirm if document is very large
        size_mb = self.current_document_path.stat().st_size / (1024 * 1024)
        if size_mb > 20:  # More than 20MB
            reply = QMessageBox.question(
                self, "Large Document", 
                f"The selected document is {size_mb:.1f} MB, which may take "
                f"a significant amount of time to process. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        # Get model context size
        model_id = self.config.get('CURRENT_MODEL_ID')
        context_size = 128000  # Default
        
        if model_id:
            model_info = self.model_manager.get_model_info(model_id)
            if model_info:
                context_size = model_info.get('context_window', 128000)
        
        # Quick token estimate check
        quick_estimate = self.current_document_path.stat().st_size // 4
        if quick_estimate > context_size * 1.1:  # 10% buffer
            reply = QMessageBox.question(
                self, "Document Too Large", 
                f"The selected document may be too large for the current model's "
                f"context window ({context_size:,} tokens). Continue anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        # Update status
        self.status_label.setText(f"Processing {self.current_document_path.name}...")
        self.progress_bar.setValue(0)
        
        # Disable buttons during processing
        self.process_button.setEnabled(False)
        self.estimate_button.setEnabled(False)
        self.remove_doc_button.setEnabled(False) # Disable remove during processing

        # Start processing
        self.document_processor.process_document(
            self.current_document_path,
            set_as_master=self.set_master_checkbox.isChecked()
        )
    
    @pyqtSlot(str, int, bool)
    def on_token_estimation_complete(self, document_id: str, token_count: int, fits_context: bool):
        """Handle token estimation completion"""
        self.token_count_label.setText(f"{token_count:,}")
        
        if fits_context:
            self.context_fit_label.setText("Fits in context")
            self.context_fit_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.context_fit_label.setText("Too large for context")
            self.context_fit_label.setStyleSheet("color: #F44336; font-weight: bold;")
            
        self.status_label.setText(f"Token estimation complete: {token_count:,} tokens")
    
    @pyqtSlot(str, int)
    def on_processing_progress(self, document_id: str, progress: int):
        """Handle processing progress update"""
        self.progress_bar.setValue(progress)
    
    @pyqtSlot(str, bool, str)
    def on_processing_complete(self, document_id: str, success: bool, message: str):
        """Handle processing completion"""
        if success:
            self.status_label.setText(f"Processing complete: {message}")
            self.progress_bar.setValue(100)
            # Get KV cache path from message (updated for .llama_cache)
            import re
            # Look for a path ending in .llama_cache in the message
            cache_path_match = re.search(r'at\s+(.*?\.llama_cache)', message)
            cache_path = cache_path_match.group(1) if cache_path_match else None

            if not cache_path:
                 # Fallback: Try to find the path in the document registry based on document_id
                 doc_info = self.document_processor.get_document_registry().get(document_id)
                 if doc_info:
                     cache_path = doc_info.get('kv_cache_path')

            # Emit signal if path found
            if cache_path:
                self.kv_cache_created.emit(cache_path, True)
            else:
                 logging.warning("Could not determine cache path from success message or registry.")
                 # Emit success but without a path? Or emit failure?
                 # Let's emit success but log the issue. The cache tab should still pick it up on refresh.
                 self.kv_cache_created.emit("", True) # Emit success, but path unknown

        else:
            self.status_label.setText(f"Processing failed: {message}")
            self.progress_bar.setValue(0)
            
            # Emit signal with failure
            self.kv_cache_created.emit("", False)
        
        # Re-enable buttons (only if a document is still selected)
        if self.current_document_path:
            self.process_button.setEnabled(True)
            self.estimate_button.setEnabled(True)
            self.remove_doc_button.setEnabled(True)


    def on_model_changed(self, model_id: str):
        """Handle model change"""
        if model_id:
            model_info = self.model_manager.get_model_info(model_id)
            if model_info:
                self.model_label.setText(f"Current Model: {model_info.get('name', model_id)}")
                context_size = model_info.get('context_window', 128000)
                self.context_label.setText(f"Context Size: {context_size:,} tokens")
                
                # Update document info if a document is selected
                if self.current_document_path:
                    self.update_document_info(self.current_document_path)
