#!/usr/bin/env python3
"""
Model tab for LlamaCag UI
Provides an interface for managing models with automatic downloading.
"""
import os
import sys
import requests
import threading
import time
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QProgressBar, QMessageBox,
    QComboBox, QDialog, QGridLayout, QGroupBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from core.model_manager import ModelManager
from utils.config import ConfigManager

class ModelDownloadDialog(QDialog):
    """Dialog for downloading models"""
    def __init__(self, model_manager, parent=None):
        super().__init__(parent)
        self.model_manager = model_manager
        self.selected_model = None
        self.setup_ui()
        self.connect_signals()
        self.load_models()
        
    def setup_ui(self):
        """Set up the user interface"""
        self.setWindowTitle("Download Model")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Select a Model to Download")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        # Description
        description = QLabel("Choose from the list of available large context window models.")
        layout.addWidget(description)
        
        # Recommendation label
        recommendation = QLabel("Recommended for beginners: Gemma 3 4B Instruct (Q4_K_M)")
        recommendation.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(recommendation)
        
        # Model selection group
        model_group = QGroupBox("Available Models")
        model_layout = QVBoxLayout(model_group)
        
        # Model type selection
        self.model_type_combo = QComboBox()
        self.model_type_combo.addItem("Gemma 3 Models", "gemma3")
        self.model_type_combo.addItem("Llama 3 Models", "llama3")
        self.model_type_combo.addItem("Mistral Models", "mistral")
        model_layout.addWidget(self.model_type_combo)
        
        # Model list
        self.model_list = QListWidget()
        model_layout.addWidget(self.model_list)
        
        layout.addWidget(model_group)
        
        # Model info
        info_group = QGroupBox("Model Information")
        info_layout = QVBoxLayout(info_group)
        self.model_info_label = QLabel("Select a model to see details")
        self.model_info_label.setWordWrap(True)
        info_layout.addWidget(self.model_info_label)
        layout.addWidget(info_group)
        
        # Progress bar
        self.progress_frame = QFrame()
        progress_layout = QVBoxLayout(self.progress_frame)
        
        self.progress_label = QLabel("Ready to download")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_frame.setVisible(False)
        layout.addWidget(self.progress_frame)
        
        # Button row
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        
        self.download_button = QPushButton("Download Selected Model")
        self.download_button.setEnabled(False)
        self.download_button.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; padding: 8px 16px; }"
        )
        button_layout.addWidget(self.download_button)
        
        layout.addLayout(button_layout)
    
    def connect_signals(self):
        """Connect signals"""
        self.model_type_combo.currentIndexChanged.connect(self.on_model_type_changed)
        self.model_list.itemSelectionChanged.connect(self.on_model_selected)
        self.download_button.clicked.connect(self.download_model)
        self.cancel_button.clicked.connect(self.reject)
        
        # Model manager signals
        self.model_manager.download_progress.connect(self.on_download_progress)
        self.model_manager.download_complete.connect(self.on_download_complete)
    
    def load_models(self):
        """Load available model options"""
        self.on_model_type_changed()
    
    def on_model_type_changed(self):
        """Handle model type selection change"""
        self.model_list.clear()
        model_type = self.model_type_combo.currentData()
        
        # Define available models based on type
        models = []
        
        if model_type == "gemma3":
            models = [
                {
                    "id": "gemma-3-4b-it-Q4_K_M", 
                    "name": "Gemma 3 4B Instruct (Q4_K_M)", 
                    "url": "https://huggingface.co/bartowski/google_gemma-3-4b-it-GGUF/resolve/main/gemma-3-4b-it-Q4_K_M.gguf",
                    "size": "2.49GB",
                    "parameters": "4 billion",
                    "context": "128K tokens",
                    "description": "Google's Gemma 3 4B instruction-tuned, good quality/size balance"
                },
                {
                    "id": "gemma-3-4b-it-Q5_K_M", 
                    "name": "Gemma 3 4B Instruct (Q5_K_M)", 
                    "url": "https://huggingface.co/bartowski/google_gemma-3-4b-it-GGUF/resolve/main/gemma-3-4b-it-Q5_K_M.gguf",
                    "size": "2.83GB",
                    "parameters": "4 billion",
                    "context": "128K tokens",
                    "description": "Google's Gemma 3 4B instruction-tuned, high quality"
                },
                {
                    "id": "gemma-3-4b-Q4_K_M", 
                    "name": "Gemma 3 4B Base (Q4_K_M)", 
                    "url": "https://huggingface.co/bartowski/google_gemma-3-4b-GGUF/resolve/main/gemma-3-4b.Q4_K_M.gguf",
                    "size": "2.49GB",
                    "parameters": "4 billion",
                    "context": "128K tokens",
                    "description": "Google's Gemma 3 4B base model (not instruction-tuned)"
                }
            ]
        elif model_type == "llama3":
            models = [
                {
                    "id": "llama-3-8b-instruct-Q4_K_M", 
                    "name": "Llama 3 8B Instruct (Q4_K_M)", 
                    "url": "https://huggingface.co/TheBloke/Llama-3-8B-Instruct-GGUF/resolve/main/llama-3-8b-instruct.Q4_K_M.gguf",
                    "size": "4.7GB",
                    "parameters": "8 billion",
                    "context": "128K tokens",
                    "description": "Meta's Llama 3 8B instruction-tuned model, good quality/size balance"
                },
                {
                    "id": "llama-3-8b-Q4_K_M", 
                    "name": "Llama 3 8B (Q4_K_M)", 
                    "url": "https://huggingface.co/TheBloke/Llama-3-8B-GGUF/resolve/main/llama-3-8b.Q4_K_M.gguf",
                    "size": "4.7GB",
                    "parameters": "8 billion",
                    "context": "128K tokens",
                    "description": "Meta's Llama 3 8B base model, good quality/size balance"
                }
            ]
        elif model_type == "mistral":
            models = [
                {
                    "id": "mistral-7b-instruct-Q4_K_M", 
                    "name": "Mistral 7B Instruct (Q4_K_M)", 
                    "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                    "size": "4.1GB",
                    "parameters": "7 billion",
                    "context": "128K tokens",
                    "description": "Mistral's 7B instruction-tuned model, good quality/size balance"
                }
            ]
        
        # Add models to list
        for model in models:
            item = QListWidgetItem(f"{model['name']} ({model['size']})")
            item.setData(Qt.UserRole, model)
            item.setToolTip(model['description'])
            self.model_list.addItem(item)
    
    def on_model_selected(self):
        """Handle model selection"""
        items = self.model_list.selectedItems()
        if items:
            self.selected_model = items[0].data(Qt.UserRole)
            self.download_button.setEnabled(True)
            
            # Update info label
            model = self.selected_model
            info_text = f"""
<b>Model:</b> {model['name']}
<b>Parameters:</b> {model['parameters']}
<b>Size:</b> {model['size']}
<b>Context:</b> {model['context']}

<b>Description:</b> {model['description']}
"""
            self.model_info_label.setText(info_text)
        else:
            self.selected_model = None
            self.download_button.setEnabled(False)
            self.model_info_label.setText("Select a model to see details")
    
    def download_model(self):
        """Download the selected model"""
        if not self.selected_model:
            return
            
        # Show progress UI
        self.progress_frame.setVisible(True)
        self.progress_label.setText(f"Downloading {self.selected_model['name']}...")
        self.progress_bar.setValue(0)
        
        # Disable controls
        self.model_list.setEnabled(False)
        self.model_type_combo.setEnabled(False)
        self.download_button.setEnabled(False)
        
        # Get model ID and URL
        model_id = self.selected_model['id']
        model_url = self.selected_model['url']
        
        # Start download
        self.model_manager.download_model(model_id, model_url)
    
    def on_download_progress(self, model_id: str, progress: int):
        """Handle download progress update"""
        if self.selected_model and model_id == self.selected_model['id']:
            self.progress_bar.setValue(progress)
            self.progress_label.setText(f"Downloading {self.selected_model['name']}... {progress}%")
    
    def on_download_complete(self, model_id: str, success: bool, message: str):
        """Handle download completion"""
        if self.selected_model and model_id == self.selected_model['id']:
            if success:
                self.progress_label.setText(f"Download complete: {message}")
                self.progress_bar.setValue(100)
                
                # Accept dialog after a short delay
                QMessageBox.information(
                    self,
                    "Download Complete",
                    f"Successfully downloaded {self.selected_model['name']}!"
                )
                self.accept()
            else:
                self.progress_label.setText(f"Download failed: {message}")
                
                # Re-enable controls
                self.model_list.setEnabled(True)
                self.model_type_combo.setEnabled(True)
                self.download_button.setEnabled(True)
                
                QMessageBox.warning(
                    self,
                    "Download Failed",
                    f"Failed to download {self.selected_model['name']}: {message}\n\nYou may need to manually download this model from the website."
                )

class ModelTab(QWidget):
    """Model management tab"""
    # Signals
    model_changed = pyqtSignal(str)  # model_id
    
    def __init__(self, model_manager: ModelManager, config_manager: ConfigManager):
        """Initialize model tab"""
        super().__init__()
        self.model_manager = model_manager
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        
        # Set up UI
        self.setup_ui()
        
        # Connect signals
        self.connect_signals()
        
        # Load models
        self.load_models()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Header label
        header = QLabel("Model Management")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        # Description
        description = QLabel("Download and select AI models to use with LlamaCag UI.")
        layout.addWidget(description)
        
        # Model info panel
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_frame.setStyleSheet("background-color: #f5f9ff;")
        info_layout = QVBoxLayout(info_frame)
        
        self.current_model_label = QLabel("Current Model: None")
        self.current_model_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.current_model_label)
        
        self.model_details_label = QLabel("No model selected")
        info_layout.addWidget(self.model_details_label)
        
        layout.addWidget(info_frame)
        
        # "Available Models" label
        available_label = QLabel("Available Models:")
        layout.addWidget(available_label)
        
        # Model list
        self.model_list = QListWidget()
        layout.addWidget(self.model_list)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Download model button
        self.download_button = QPushButton("Download Model")
        self.download_button.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; padding: 8px 16px; }"
        )
        button_layout.addWidget(self.download_button)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        button_layout.addWidget(self.refresh_button)
        
        # Manual download info
        self.manual_button = QPushButton("Manual Download Info")
        button_layout.addWidget(self.manual_button)
        
        layout.addLayout(button_layout)
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
    
    def connect_signals(self):
        """Connect signals between components"""
        # List signals
        self.model_list.itemSelectionChanged.connect(self.on_model_selected)
        
        # Button signals
        self.download_button.clicked.connect(self.show_download_dialog)
        self.refresh_button.clicked.connect(self.load_models)
        self.manual_button.clicked.connect(self.show_manual_download_info)
        
        # Model manager signals
        self.model_manager.download_progress.connect(self.on_download_progress)
        self.model_manager.download_complete.connect(self.on_download_complete)
        self.model_manager.model_list_updated.connect(self.load_models)
    
    def load_models(self):
        """Load available models"""
        # Save current selection
        current_selected = None
        items = self.model_list.selectedItems()
        if items:
            current_selected = items[0].data(Qt.UserRole)
        
        self.model_list.clear()
        
        # Get available models
        models = self.model_manager.get_available_models()
        
        # Sort by name
        models.sort(key=lambda x: x.get('name', ''))
        
        # Add to list
        for model in models:
            # Only show GGUF models
            if not model.get('filename', '').lower().endswith('.gguf'):
                continue
                
            item = QListWidgetItem(f"{model.get('name', model.get('id', 'Unknown'))}")
            item.setData(Qt.UserRole, model.get('id'))
            
            # Add tooltip with additional info
            params = model.get('parameters', 'Unknown')
            ctx = model.get('context_window', 'Unknown')
            tooltip = f"Parameters: {params}\nContext Window: {ctx}\nPath: {model.get('path', '')}"
            item.setToolTip(tooltip)
            
            # Select if current model or previously selected
            if ((current_selected and model.get('id') == current_selected) or
                (not current_selected and self.config.get('CURRENT_MODEL_ID') == model.get('id'))):
                item.setSelected(True)
            
            self.model_list.addItem(item)
        
        # Update status
        self.status_label.setText(f"Found {len(models)} models")
        
        # Update current model display
        current_model_id = self.config.get('CURRENT_MODEL_ID')
        if current_model_id:
            model_info = self.model_manager.get_model_info(current_model_id)
            if model_info:
                self.current_model_label.setText(f"Current Model: {model_info.get('name', current_model_id)}")
                
                # Update details
                context = model_info.get('context_window', 'Unknown')
                params = model_info.get('parameters', 'Unknown')
                quant = model_info.get('quantization', 'Unknown')
                details = f"Context Window: {context} tokens | Parameters: {params} | Quantization: {quant}"
                self.model_details_label.setText(details)
    
    def on_model_selected(self):
        """Handle model selection change"""
        items = self.model_list.selectedItems()
        if not items:
            return
            
        # Get selected model
        model_id = items[0].data(Qt.UserRole)
        
        # Update config
        self.config['CURRENT_MODEL_ID'] = model_id
        self.config_manager.save_config()
        
        # Emit signal
        self.model_changed.emit(model_id)
        
        # Update status
        model_info = self.model_manager.get_model_info(model_id)
        if model_info:
            self.status_label.setText(f"Selected model: {model_info.get('name', model_id)}")
            
            # Update current model display
            self.current_model_label.setText(f"Current Model: {model_info.get('name', model_id)}")
            
            # Update details
            context = model_info.get('context_window', 'Unknown')
            params = model_info.get('parameters', 'Unknown')
            quant = model_info.get('quantization', 'Unknown')
            details = f"Context Window: {context} tokens | Parameters: {params} | Quantization: {quant}"
            self.model_details_label.setText(details)
    
    def show_download_dialog(self):
        """Show dialog to download a model"""
        dialog = ModelDownloadDialog(self.model_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            # Refresh model list
            self.load_models()
    
    def show_manual_download_info(self):
        """Show information about manual downloading"""
        info_text = """<html>
<h3>Manual Model Download Guide</h3>
<p>If automatic downloading isn't working, you can download models manually:</p>
<ol>
  <li>Go to <a href="https://huggingface.co/bartowski/google_gemma-3-4b-it-GGUF">https://huggingface.co/bartowski/google_gemma-3-4b-it-GGUF</a></li>
  <li>Download the "gemma-3-4b-it-Q4_K_M.gguf" file (recommended for most users)</li>
  <li>Save it to your models directory: ~/Documents/llama.cpp/models/</li>
  <li>Click "Refresh" in the app to detect the model</li>
</ol>
<p><b>About GGUF Files:</b> These are special quantized versions of AI models that work with llama.cpp</p>
<p><b>About Quantization:</b> Q4_K_M balances quality and file size; higher numbers (Q5, Q6, Q8) mean higher quality but larger files</p>
</html>"""
        
        QMessageBox.information(
            self,
            "Manual Download Information",
            info_text
        )
    
    def on_download_progress(self, model_id: str, progress: int):
        """Handle download progress update"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"Downloading {model_id}... {progress}%")
    
    def on_download_complete(self, model_id: str, success: bool, message: str):
        """Handle download completion"""
        self.progress_bar.setVisible(False)
        if success:
            self.status_label.setText(f"Download complete: {message}")
            # Reload models
            self.load_models()
        else:
            self.status_label.setText(f"Download failed: {message}")
            QMessageBox.warning(
                self,
                "Download Failed",
                f"Failed to download model {model_id}:\n{message}\n\nYou may need to download the model manually."
            )