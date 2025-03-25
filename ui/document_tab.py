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

from core.document_processor import DocumentProcessor
from core.model_manager import ModelManager
from utils.config import ConfigManager
from utils.token_counter import estimate_tokens_for_file


class DocumentTab(QWidget):
    """Document processing tab for creating KV caches"""
    
    # Signals
    kv_cache_created = pyqtSignal(str, bool)  # cache_path, success
    
    def __init__(self, document_processor: DocumentProcessor, model_manager: ModelManager, 
                 config_manager: ConfigManager):
        """Initialize document tab"""
        super().__init__()
        
        self.document_processor = document_processor
        self.model_manager = model_manager
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
        model_frame.setFrameShape(QFrame.StyledPanel)
        model_frame.setStyleSheet("background-color: #f5f9ff;")
        model_layout = QHBoxLayout(model_frame)
        
        self.model_label = QLabel("Current Model: None")
        self.model_label.setStyleSheet("color: #000000; font-weight: bold;")
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
        
        self.clear_docs_button = QPushButton("Clear Selection")
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
        
        info_layout.addWidget(QLabel("Selected Document:"), 0, 0)
        self.doc_name_label = QLabel("None")
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
        
        # Set initial splitter sizes
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter, 1)
    
    def connect_signals(self):
        """Connect signals between components"""
        # Button signals
        self.select_file_button.clicked.connect(self.select_document_file)
        self.select_folder_button.clicked.connect(self.select_document_folder)
        self.clear_docs_button.clicked.connect(self.clear_document_selection)
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
    
    def clear_document_selection(self):
        """Clear the document selection"""
        self.document_list.clear()
        self.selected_documents = []
        
        # Update document info
        self.update_document_info(None)
        
        # Save to config
        self.config['RECENT_DOCUMENTS'] = []
        self.config_manager.save_config()
    
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
            return
            
        # Document exists?
        if not document_path.exists():
            self.doc_name_label.setText(f"{document_path.name} (not found)")
            self.file_size_label.setText("N/A")
            self.token_count_label.setText("N/A")
            self.context_fit_label.setText("N/A")
            self.estimate_button.setEnabled(False)
            self.process_button.setEnabled(False)
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
            
            # Get KV cache path from message (bit of a hack)
            import re
            cache_path_match = re.search(r'at (.*?\.bin)', message)
            cache_path = cache_path_match.group(1) if cache_path_match else None
            
            # Emit signal
            if cache_path:
                self.kv_cache_created.emit(cache_path, True)
        else:
            self.status_label.setText(f"Processing failed: {message}")
            self.progress_bar.setValue(0)
            
            # Emit signal with failure
            self.kv_cache_created.emit("", False)
        
        # Re-enable buttons
        self.process_button.setEnabled(True)
        self.estimate_button.setEnabled(True)
    
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
