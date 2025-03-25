#!/usr/bin/env python3
"""
Model tab for LlamaCag UI
Provides an interface for managing models.
"""
import os
import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from core.model_manager import ModelManager
from utils.config import ConfigManager
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
        button_layout.addWidget(self.download_button)
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        button_layout.addWidget(self.refresh_button)
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
        self.download_button.clicked.connect(self.download_model)
        self.refresh_button.clicked.connect(self.load_models)
        # Model manager signals
        self.model_manager.download_progress.connect(self.on_download_progress)
        self.model_manager.download_complete.connect(self.on_download_complete)
        self.model_manager.model_list_updated.connect(self.load_models)
    def load_models(self):
        """Load available models"""
        self.model_list.clear()
        # Get available models
        models = self.model_manager.get_available_models()
        # Sort by name
        models.sort(key=lambda x: x.get('name', ''))
        # Add to list
        for model in models:
            item = QListWidgetItem(f"{model.get('name', model.get('id', 'Unknown'))}")
            item.setData(Qt.UserRole, model.get('id'))
            # Select if current model
            current_model_id = self.config.get('CURRENT_MODEL_ID')
            if current_model_id and model.get('id') == current_model_id:
                item.setSelected(True)
            self.model_list.addItem(item)
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
    def download_model(self):
        """Download a model"""
        models_dir = os.path.expanduser('~/Documents/llama.cpp/models/')
        # Create models directory if it doesn't exist
        os.makedirs(models_dir, exist_ok=True)
        QMessageBox.information(
            self,
            "Download Model",
            f"Automatic model downloading is not yet implemented.\n\n"
            f"To use a large context window model:\n\n"
            f"1. Download a GGUF model like Gemma 3 4B (128K) from:\n"
            f"   https://huggingface.co/bartowski/gemma-4b-GGUF/resolve/main/gemma-4b-q4_k_m.gguf\n\n"
            f"2. Save it to your models directory:\n"
            f"   {models_dir}\n\n"
            f"3. Once downloaded, click the 'Refresh' button to detect the model."
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
                f"Failed to download model {model_id}:\n{message}"
            )