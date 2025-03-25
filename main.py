#!/usr/bin/env python3
"""
LlamaCag UI - A user-friendly interface for llama-cag-n8n
This application provides a GUI for managing large context window models,
creating KV caches from documents, and interacting with the model.
"""
import sys
import os
import logging
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QSettings
from ui.main_window import MainWindow
from utils.config import ConfigManager
from utils.logging_utils import setup_logging
from core.llama_manager import LlamaManager
from core.model_manager import ModelManager
from core.cache_manager import CacheManager
from core.document_processor import DocumentProcessor
from core.chat_engine import ChatEngine
from core.n8n_interface import N8nInterface
VERSION = "0.1.0"
def check_prerequisites():
    """Check if essential prerequisites are met"""
    # Check for Python version
    if sys.version_info < (3, 8):
        show_error("Python 3.8 or higher is required.")
        return False
    return True
def show_error(message):
    """Show error message and exit"""
    if QApplication.instance() is None:
        # Create a minimal application instance if one doesn't exist
        app = QApplication(sys.argv)
    error_box = QMessageBox()
    error_box.setIcon(QMessageBox.Critical)
    error_box.setWindowTitle("LlamaCag UI - Error")
    error_box.setText(message)
    error_box.setStandardButtons(QMessageBox.Ok)
    error_box.exec_()
def main():
    """Application entry point"""
    # Setup logging
    setup_logging()
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    # Initialize application
    app = QApplication(sys.argv)
    app.setApplicationName("LlamaCagUI")
    app.setApplicationVersion(VERSION)
    # Load configuration
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
    except Exception as e:
        logging.error(f"Failed to load configuration: {str(e)}")
        show_error(f"Failed to load configuration: {str(e)}")
        sys.exit(1)
    # Initialize core components
    llama_manager = LlamaManager(config)
    model_manager = ModelManager(config)
    cache_manager = CacheManager(config)
    n8n_interface = N8nInterface(config)
    # Initialize dependent components
    document_processor = DocumentProcessor(config, llama_manager, model_manager, cache_manager)
    chat_engine = ChatEngine(config, llama_manager, model_manager, cache_manager)
    # Check if llama.cpp is installed
    if not llama_manager.is_installed():
        response = QMessageBox.question(
            None,
            "LlamaCag UI - Setup",
            "llama.cpp is not installed. Would you like to install it now?",
            QMessageBox.Yes | QMessageBox.No
        )
        if response == QMessageBox.Yes:
            # Show installation dialog
            try:
                llama_manager.install()
            except Exception as e:
                logging.error(f"Installation failed: {str(e)}")
                show_error(f"Installation failed: {str(e)}")
                sys.exit(1)
        else:
            show_error("llama.cpp is required for this application to function.")
            sys.exit(1)
    # Create and show main window
    main_window = MainWindow(
        config_manager,
        llama_manager,
        model_manager,
        cache_manager,
        document_processor,
        chat_engine,
        n8n_interface
    )
    main_window.show()
    # Start the event loop
    sys.exit(app.exec_())
if __name__ == "__main__":
    main()