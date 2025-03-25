#!/usr/bin/env python3
"""
Settings tab for LlamaCag UI
Provides an interface for configuring the application.
"""
import os
import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox, QFormLayout, QFileDialog,
    QCheckBox, QSpinBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from core.llama_manager import LlamaManager
from core.n8n_interface import N8nInterface
from utils.config import ConfigManager
class SettingsTab(QWidget):
    """Settings tab for configuration"""
    # Signals
    settings_changed = pyqtSignal()
    def __init__(self, config_manager: ConfigManager,
                 llama_manager: LlamaManager, n8n_interface: N8nInterface):
        """Initialize settings tab"""
        super().__init__()
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        self.llama_manager = llama_manager
        self.n8n_interface = n8n_interface
        # Set up UI
        self.setup_ui()
        # Connect signals
        self.connect_signals()
        # Load settings
        self.load_settings()
    def setup_ui(self):
        """Set up the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        # Header label
        header = QLabel("Settings")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        # Paths group
        paths_group = QGroupBox("Paths")
        paths_layout = QFormLayout(paths_group)
        # llamacpp_path
        self.llamacpp_path_edit = QLineEdit()
        self.llamacpp_path_button = QPushButton("Browse...")
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.llamacpp_path_edit)
        path_layout.addWidget(self.llamacpp_path_button)
        paths_layout.addRow("llama.cpp Path:", path_layout)
        # models_path
        self.models_path_edit = QLineEdit()
        self.models_path_button = QPushButton("Browse...")
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.models_path_edit)
        path_layout.addWidget(self.models_path_button)
        paths_layout.addRow("Models Path:", path_layout)
        # kv_cache_path
        self.kv_cache_path_edit = QLineEdit()
        self.kv_cache_path_button = QPushButton("Browse...")
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.kv_cache_path_edit)
        path_layout.addWidget(self.kv_cache_path_button)
        paths_layout.addRow("KV Cache Path:", path_layout)
        # temp_path
        self.temp_path_edit = QLineEdit()
        self.temp_path_button = QPushButton("Browse...")
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.temp_path_edit)
        path_layout.addWidget(self.temp_path_button)
        paths_layout.addRow("Temp Path:", path_layout)
        # documents_path
        self.documents_path_edit = QLineEdit()
        self.documents_path_button = QPushButton("Browse...")
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.documents_path_edit)
        path_layout.addWidget(self.documents_path_button)
        paths_layout.addRow("Documents Path:", path_layout)
        layout.addWidget(paths_group)
        # Model settings group
        model_group = QGroupBox("Model Settings")
        model_layout = QFormLayout(model_group)
        # threads
        self.threads_spin = QSpinBox()
        self.threads_spin.setMinimum(1)
        self.threads_spin.setMaximum(64)
        model_layout.addRow("Threads:", self.threads_spin)
        # batch_size
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setMinimum(1)
        self.batch_size_spin.setMaximum(4096)
        model_layout.addRow("Batch Size:", self.batch_size_spin)
        layout.addWidget(model_group)
        # n8n settings group
        n8n_group = QGroupBox("n8n Integration")
        n8n_layout = QFormLayout(n8n_group)
        # n8n_host
        self.n8n_host_edit = QLineEdit()
        n8n_layout.addRow("n8n Host:", self.n8n_host_edit)
        # n8n_port
        self.n8n_port_spin = QSpinBox()
        self.n8n_port_spin.setMinimum(1)
        self.n8n_port_spin.setMaximum(65535)
        n8n_layout.addRow("n8n Port:", self.n8n_port_spin)
        # n8n controls
        n8n_buttons = QHBoxLayout()
        self.n8n_start_button = QPushButton("Start n8n")
        self.n8n_stop_button = QPushButton("Stop n8n")
        self.n8n_status_label = QLabel("n8n Status: Unknown")
        n8n_buttons.addWidget(self.n8n_start_button)
        n8n_buttons.addWidget(self.n8n_stop_button)
        n8n_buttons.addWidget(self.n8n_status_label)
        n8n_layout.addRow("n8n Controls:", n8n_buttons)
        layout.addWidget(n8n_group)
        # Button layout
        button_layout = QHBoxLayout()
        # Save button
        self.save_button = QPushButton("Save Settings")
        button_layout.addWidget(self.save_button)
        # Reset button
        self.reset_button = QPushButton("Reset to Defaults")
        button_layout.addWidget(self.reset_button)
        layout.addLayout(button_layout)
        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
    def connect_signals(self):
        """Connect signals between components"""
        # Path browser buttons
        self.llamacpp_path_button.clicked.connect(lambda: self.browse_path(self.llamacpp_path_edit, "llama.cpp Path"))
        self.models_path_button.clicked.connect(lambda: self.browse_path(self.models_path_edit, "Models Path"))
        self.kv_cache_path_button.clicked.connect(lambda: self.browse_path(self.kv_cache_path_edit, "KV Cache Path"))
        self.temp_path_button.clicked.connect(lambda: self.browse_path(self.temp_path_edit, "Temp Path"))
        self.documents_path_button.clicked.connect(lambda: self.browse_path(self.documents_path_edit, "Documents Path"))
        # Save/reset buttons
        self.save_button.clicked.connect(self.save_settings)
        self.reset_button.clicked.connect(self.reset_settings)
        # n8n controls
        self.n8n_start_button.clicked.connect(self.start_n8n)
        self.n8n_stop_button.clicked.connect(self.stop_n8n)
        # n8n interface signals
        self.n8n_interface.status_changed.connect(self.update_n8n_status)
    def load_settings(self):
        """Load settings from config"""
        # Paths
        self.llamacpp_path_edit.setText(os.path.expanduser(self.config.get('LLAMACPP_PATH', '~/Documents/llama.cpp')))
        self.models_path_edit.setText(os.path.expanduser(self.config.get('LLAMACPP_MODEL_PATH', '~/Documents/llama.cpp/models')))
        self.kv_cache_path_edit.setText(os.path.expanduser(self.config.get('LLAMACPP_KV_CACHE_DIR', '~/cag_project/kv_caches')))
        self.temp_path_edit.setText(os.path.expanduser(self.config.get('LLAMACPP_TEMP_DIR', '~/cag_project/temp_chunks')))
        self.documents_path_edit.setText(os.path.expanduser(self.config.get('DOCUMENTS_FOLDER', '~/Documents/cag_documents')))
        # Model settings
        self.threads_spin.setValue(int(self.config.get('LLAMACPP_THREADS', '4')))
        self.batch_size_spin.setValue(int(self.config.get('LLAMACPP_BATCH_SIZE', '1024')))
        # n8n settings
        self.n8n_host_edit.setText(self.config.get('N8N_HOST', 'localhost'))
        self.n8n_port_spin.setValue(int(self.config.get('N8N_PORT', '5678')))
        # Update n8n status
        self.update_n8n_status(self.n8n_interface.is_running())
    def browse_path(self, line_edit, title):
        """Browse for a directory path"""
        current_path = os.path.expanduser(line_edit.text())
        path = QFileDialog.getExistingDirectory(
            self, f"Select {title}", current_path
        )
        if path:
            line_edit.setText(path)
    def save_settings(self):
        """Save settings to config"""
        # Paths
        self.config['LLAMACPP_PATH'] = self.llamacpp_path_edit.text()
        self.config['LLAMACPP_MODEL_PATH'] = self.models_path_edit.text()
        self.config['LLAMACPP_KV_CACHE_DIR'] = self.kv_cache_path_edit.text()
        self.config['LLAMACPP_TEMP_DIR'] = self.temp_path_edit.text()
        self.config['DOCUMENTS_FOLDER'] = self.documents_path_edit.text()
        # Model settings
        self.config['LLAMACPP_THREADS'] = str(self.threads_spin.value())
        self.config['LLAMACPP_BATCH_SIZE'] = str(self.batch_size_spin.value())
        # n8n settings
        self.config['N8N_HOST'] = self.n8n_host_edit.text()
        self.config['N8N_PORT'] = str(self.n8n_port_spin.value())
        # Save config
        self.config_manager.save_config()
        # Update status
        self.status_label.setText("Settings saved")
        # Emit signal
        self.settings_changed.emit()
    def reset_settings(self):
        """Reset settings to defaults"""
        # Confirm
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        # Set defaults
        self.llamacpp_path_edit.setText('~/Documents/llama.cpp')
        self.models_path_edit.setText('~/Documents/llama.cpp/models')
        self.kv_cache_path_edit.setText('~/cag_project/kv_caches')
        self.temp_path_edit.setText('~/cag_project/temp_chunks')
        self.documents_path_edit.setText('~/Documents/cag_documents')
        self.threads_spin.setValue(4)
        self.batch_size_spin.setValue(1024)
        self.n8n_host_edit.setText('localhost')
        self.n8n_port_spin.setValue(5678)
        # Update status
        self.status_label.setText("Settings reset to defaults (not saved)")
    def start_n8n(self):
        """Start n8n services"""
        success = self.n8n_interface.start_services()
        if success:
            self.status_label.setText("n8n services started")
        else:
            self.status_label.setText("Failed to start n8n services")
            QMessageBox.warning(
                self,
                "n8n Start Failed",
                "Failed to start n8n services. Check the logs for details."
            )
    def stop_n8n(self):
        """Stop n8n services"""
        success = self.n8n_interface.stop_services()
        if success:
            self.status_label.setText("n8n services stopped")
        else:
            self.status_label.setText("Failed to stop n8n services")
            QMessageBox.warning(
                self,
                "n8n Stop Failed",
                "Failed to stop n8n services. Check the logs for details."
            )
    def update_n8n_status(self, is_running: bool):
        """Update n8n status display"""
        if is_running:
            self.n8n_status_label.setText("n8n Status: Running")
            self.n8n_status_label.setStyleSheet("color: green;")
            self.n8n_start_button.setEnabled(False)
            self.n8n_stop_button.setEnabled(True)
        else:
            self.n8n_status_label.setText("n8n Status: Stopped")
            self.n8n_status_label.setStyleSheet("color: red;")
            self.n8n_start_button.setEnabled(True)
            self.n8n_stop_button.setEnabled(False)