#!/usr/bin/env python3
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
        
        # Model and KV cache info panel
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_frame.setStyleSheet("background-color: #F5F9FF; color: #000000;")
        info_layout = QHBoxLayout(info_frame)
        
        # Current model info
        self.model_label = QLabel("Current Model: None")
        self.model_label.setStyleSheet("color: #000000; font-weight: bold;")
        self.model_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.model_label)
        
        # KV cache toggle
        self.kv_cache_checkbox = QCheckBox("Use KV Cache")
        self.kv_cache_checkbox.setChecked(True)
        info_layout.addWidget(self.kv_cache_checkbox)
        
        # Current KV cache info
        self.kv_cache_label = QLabel("Current KV Cache: None")
        info_layout.addWidget(self.kv_cache_label)
        
        info_layout.addStretch()
        
        # Temperature control
        temp_label = QLabel("Temperature:")
        info_layout.addWidget(temp_label)
        
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setMinimum(0)
        self.temp_slider.setMaximum(100)
        self.temp_slider.setValue(70)  # Default 0.7
        self.temp_slider.setFixedWidth(100)
        info_layout.addWidget(self.temp_slider)
        
        self.temp_value = QLabel("0.7")
        info_layout.addWidget(self.temp_value)
        
        # Max tokens
        max_tokens_label = QLabel("Max Tokens:")
        info_layout.addWidget(max_tokens_label)
        
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setMinimum(1)
        self.max_tokens_spin.setMaximum(8192)
        self.max_tokens_spin.setValue(1024)
        info_layout.addWidget(self.max_tokens_spin)
        
        layout.addWidget(info_frame)
        
        # Chat area
        chat_splitter = QSplitter(Qt.Vertical)
        chat_splitter.setChildrenCollapsible(False)
        
        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setMinimumHeight(300)
        self.chat_history.setStyleSheet(
            "QTextEdit { background-color: white; border: 1px solid #ddd; }"
        )
        chat_splitter.addWidget(self.chat_history)
        
        # Input area
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 10, 0, 0)
        
        # Message input
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setMinimumHeight(100)
        self.message_input.setMaximumHeight(200)
        input_layout.addWidget(self.message_input)
        
        # Button bar
        button_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Clear Chat")
        button_layout.addWidget(self.clear_button)
        
        self.save_button = QPushButton("Save Chat")
        button_layout.addWidget(self.save_button)
        
        self.load_button = QPushButton("Load Chat")
        button_layout.addWidget(self.load_button)
        
        button_layout.addStretch()
        
        self.send_button = QPushButton("Send")
        self.send_button.setDefault(True)
        self.send_button.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; padding: 8px 16px; }"
        )
        button_layout.addWidget(self.send_button)
        
        input_layout.addLayout(button_layout)
        chat_splitter.addWidget(input_widget)
        
        layout.addWidget(chat_splitter, 1)
        
        # Status bar
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.token_count_label = QLabel("Tokens: 0")
        status_layout.addWidget(self.token_count_label)
        
        layout.addLayout(status_layout)
    
    def connect_signals(self):
        """Connect signals between components"""
        # Button signals
        self.send_button.clicked.connect(self.send_message)
        self.clear_button.clicked.connect(self.clear_chat)
        self.save_button.clicked.connect(self.save_chat)
        self.load_button.clicked.connect(self.load_chat)
        
        # Input signals
        self.message_input.textChanged.connect(self.update_token_count)
        
        # Control signals
        self.kv_cache_checkbox.toggled.connect(self.toggle_kv_cache)
        self.temp_slider.valueChanged.connect(self.update_temperature)
        
        # Chat engine signals
        self.chat_engine.response_started.connect(self.on_response_started)
        self.chat_engine.response_chunk.connect(self.on_response_chunk)
        self.chat_engine.response_complete.connect(self.on_response_complete)
        self.chat_engine.error_occurred.connect(self.on_error)
    
    def initialize_state(self):
        """Initialize UI state from current settings"""
        # Set current model
        model_id = self.config.get('CURRENT_MODEL_ID')
        if model_id:
            model_info = self.model_manager.get_model_info(model_id)
            if model_info:
                self.model_label.setText(f"Current Model: {model_info.get('name', model_id)}")
        
        # Set current KV cache
        current_kv_cache = self.chat_engine.current_kv_cache
        if current_kv_cache:
            cache_name = Path(current_kv_cache).name
            self.kv_cache_label.setText(f"Current KV Cache: {cache_name}")
        
        # Load chat history
        self.update_chat_display()
    
    def update_chat_display(self):
        """Update chat history display"""
        self.chat_history.clear()
        
        for message in self.chat_engine.get_history():
            role = message.get('role', '')
            content = message.get('content', '')
            
            if role == 'user':
                self.add_user_message_to_display(content)
            elif role == 'assistant':
                self.add_assistant_message_to_display(content)
    
    def add_user_message_to_display(self, message: str):
        """Add a user message to the chat display"""
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Format user message
        cursor.insertHtml(
            f'<div style="margin-top: 10px;">'
            f'<div style="font-weight: bold; color: #1976D2;">You:</div>'
            f'<div style="background-color: #E3F2FD; border-radius: 5px; padding: 8px; margin: 5px 0px;">'
            f'{message.replace("\n", "<br>")}'
            f'</div></div>'
        )
        
        # Add newline
        cursor.insertBlock()
        
        # Scroll to bottom
        self.chat_history.setTextCursor(cursor)
        self.chat_history.ensureCursorVisible()
    
    def add_assistant_message_to_display(self, message: str):
        """Add an assistant message to the chat display"""
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Format assistant message
        cursor.insertHtml(
            f'<div style="margin-top: 10px;">'
            f'<div style="font-weight: bold; color: #388E3C;">Assistant:</div>'
            f'<div style="background-color: #F1F8E9; border-radius: 5px; padding: 8px; margin: 5px 0px;">'
            f'{message.replace("\n", "<br>")}'
            f'</div></div>'
        )
        
        # Add newline
        cursor.insertBlock()
        
        # Scroll to bottom
        self.chat_history.setTextCursor(cursor)
        self.chat_history.ensureCursorVisible()
    
    def append_to_assistant_message(self, text: str):
        """Append text to the last assistant message in the display"""
        # Get cursor at end
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Insert with HTML formatting
        cursor.insertHtml(text.replace("\n", "<br>"))
        
        # Scroll to bottom
        self.chat_history.setTextCursor(cursor)
        self.chat_history.ensureCursorVisible()
    
    def send_message(self):
        """Send a message to the chat engine"""
        message = self.message_input.toPlainText().strip()
        if not message:
            return
        
        # Add to display
        self.add_user_message_to_display(message)
        
        # Clear input
        self.message_input.clear()
        
        # Update status
        self.status_label.setText("Processing...")
        self.send_button.setEnabled(False)
        
        # Get parameters
        temperature = self.temp_slider.value() / 100.0
        max_tokens = self.max_tokens_spin.value()
        
        # Send to chat engine
        success = self.chat_engine.send_message(message, max_tokens, temperature)
        
        if not success:
            self.status_label.setText("Error sending message")
            self.send_button.setEnabled(True)
    
    def clear_chat(self):
        """Clear the chat history"""
        self.chat_engine.clear_history()
        self.chat_history.clear()
        self.status_label.setText("Chat cleared")
    
    def save_chat(self):
        """Save the chat history to a file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Chat History", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
            
        if not file_path.endswith('.json'):
            file_path += '.json'
            
        success = self.chat_engine.save_history(file_path)
        
        if success:
            self.status_label.setText(f"Chat history saved to {Path(file_path).name}")
        else:
            self.status_label.setText("Error saving chat history")
    
    def load_chat(self):
        """Load chat history from a file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Chat History", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_path:
            return
            
        success = self.chat_engine.load_history(file_path)
        
        if success:
            self.update_chat_display()
            self.status_label.setText(f"Chat history loaded from {Path(file_path).name}")
        else:
            self.status_label.setText("Error loading chat history")
    
    def update_token_count(self):
        """Update the token count for the current input"""
        text = self.message_input.toPlainText()
        
        # Simple estimation: ~4 chars per token
        token_count = len(text) // 4
        
        self.token_count_label.setText(f"Tokens: ~{token_count}")
    
    def toggle_kv_cache(self, enabled: bool):
        """Toggle KV cache usage"""
        self.chat_engine.toggle_kv_cache(enabled)
        
        if enabled:
            current_kv_cache = self.chat_engine.current_kv_cache
            if current_kv_cache:
                cache_name = Path(current_kv_cache).name
                self.kv_cache_label.setText(f"Current KV Cache: {cache_name}")
            else:
                self.kv_cache_label.setText("Current KV Cache: None")
        else:
            self.kv_cache_label.setText("KV Cache: Disabled")
    
    def update_temperature(self, value: int):
        """Update temperature display"""
        temperature = value / 100.0
        self.temp_value.setText(f"{temperature:.1f}")
    
    def on_model_changed(self, model_id: str):
        """Handle model change"""
        model_info = self.model_manager.get_model_info(model_id)
        if model_info:
            self.model_label.setText(f"Current Model: {model_info.get('name', model_id)}")
    
    def on_cache_selected(self, cache_path: str):
        """Handle KV cache selection"""
        if cache_path:
            cache_name = Path(cache_path).name
            self.kv_cache_label.setText(f"Current KV Cache: {cache_name}")
        else:
            self.kv_cache_label.setText("Current KV Cache: None")
    
    @pyqtSlot()
    def on_response_started(self):
        """Handle response started signal"""
        # Create a placeholder for the assistant message
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Format assistant message
        cursor.insertHtml(
            f'<div style="margin-top: 10px;">'
            f'<div style="font-weight: bold; color: #388E3C;">Assistant:</div>'
            f'<div id="current-response" style="background-color: #F1F8E9; border-radius: 5px; padding: 8px; margin: 5px 0px;">'
            f'</div></div>'
        )
        
        # Add newline
        cursor.insertBlock()
        
        # Scroll to bottom
        self.chat_history.setTextCursor(cursor)
        self.chat_history.ensureCursorVisible()
    
    @pyqtSlot(str)
    def on_response_chunk(self, chunk: str):
        """Handle response chunk signal"""
        # Append to current response
        self.append_to_assistant_message(chunk)
    
    @pyqtSlot(str, bool)
    def on_response_complete(self, response: str, success: bool):
        """Handle response complete signal"""
        if success:
            self.status_label.setText("Response complete")
        else:
            self.status_label.setText("Response failed")
            
        self.send_button.setEnabled(True)
    
    @pyqtSlot(str)
    def on_error(self, error_message: str):
        """Handle error signal"""
        self.status_label.setText(f"Error: {error_message}")
        self.send_button.setEnabled(True)
