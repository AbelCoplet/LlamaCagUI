#!/usr/bin/env python3
"""
Simplest possible cache_tab.py for LlamaCag UI
"""
import os
import sys
import time
import logging # Added missing import
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QApplication # Added QApplication import for processEvents
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

        # Explanation label
        explanation_text = """Select a cache from the list below and click 'Use Selected' to activate it for the Chat tab.
Status Colors (in Chat Tab): Green = TRUE KV Cache, Orange = Fallback/Master, Gray = Disabled, Red = Missing/Error."""
        explanation_label = QLabel(explanation_text)
        explanation_label.setWordWrap(True)
        explanation_label.setStyleSheet("font-size: 10px; color: #FFFFFF; margin-bottom: 5px;") # White text
        layout.addWidget(explanation_label)

        # Cache table
        self.cache_table = QTableWidget()
        self.cache_table.setColumnCount(3)
        self.cache_table.setHorizontalHeaderLabels([
            "Cache Name", "Size", "Document"
        ])
        # Stretch last column to fill space
        self.cache_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
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

        # Purge All button
        self.purge_all_button = QPushButton("Purge All")
        self.purge_all_button.setStyleSheet("color: red;") # Make it stand out
        button_layout.addWidget(self.purge_all_button)

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
        self.purge_all_button.clicked.connect(self.confirm_purge_all_caches) # Connect new button

        # Table signals
        self.cache_table.itemSelectionChanged.connect(self.on_cache_selected)

        # Cache manager signals
        self.cache_manager.cache_list_updated.connect(self.refresh_caches)
        self.cache_manager.cache_purged.connect(self.on_cache_purged)

    def refresh_caches(self):
        """Refresh the cache list"""
        logging.debug("CacheTab: Refreshing cache list UI.")
        try:
            # Clear the table
            self.cache_table.setRowCount(0)

            # Ask cache manager to update its internal list (if needed, controlled by scan_now=True)
            # We call it here to ensure the list is up-to-date before getting it.
            # The recursion was fixed in CacheManager, so this is safe.
            try:
                self.cache_manager.refresh_cache_list(scan_now=True)
            except Exception as e:
                logging.error(f"Error calling cache_manager.refresh_cache_list: {e}")
                QMessageBox.warning(self, "Refresh Error", f"Could not refresh cache list: {e}")
                # Continue with potentially stale list from manager

            # Get the cache list
            caches = self.cache_manager.get_cache_list()
            logging.debug(f"CacheTab: Received {len(caches)} caches from manager.")

            # Add to table
            self.cache_table.setRowCount(len(caches)) # Pre-set row count
            for i, cache in enumerate(caches):
                # Cache name (Filename)
                filename = cache.get('filename', 'Unknown')
                item_name = QTableWidgetItem(filename)
                item_name.setData(Qt.UserRole, cache.get('path', '')) # Store full path in UserRole
                item_name.setFlags(item_name.flags() & ~Qt.ItemIsEditable) # Make non-editable
                self.cache_table.setItem(i, 0, item_name)

                # Size
                size_bytes = cache.get('size', 0)
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.1f} KB"
                elif size_bytes < 1024 * 1024 * 1024:
                    size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
                item_size = QTableWidgetItem(size_str)
                item_size.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_size.setFlags(item_size.flags() & ~Qt.ItemIsEditable)
                self.cache_table.setItem(i, 1, item_size)

                # Original Document Path (or ID if path is long/missing)
                doc_path_str = cache.get('original_document', 'Unknown')
                display_doc = doc_path_str if doc_path_str != "Unknown" else cache.get('document_id', 'Unknown')
                # Optionally shorten long paths
                # if len(display_doc) > 50: display_doc = "..." + display_doc[-47:] # Alternative: Tooltip
                item_doc = QTableWidgetItem(display_doc)
                item_doc.setFlags(item_doc.flags() & ~Qt.ItemIsEditable)
                # item_doc.setToolTip(doc_path_str) # Show full path in tooltip
                # Word wrap is handled by the view, not the item itself for QTableWidget
                self.cache_table.setItem(i, 2, item_doc)

            self.cache_table.resizeColumnsToContents()
            self.cache_table.setWordWrap(True) # Enable word wrap for the table view
            # Update status
            self.status_label.setText(f"{len(caches)} caches listed.")
            logging.debug("CacheTab: UI refresh complete.")

        except Exception as e:
            logging.exception("Error refreshing cache tab UI.")
            self.status_label.setText("Error refreshing caches UI.")

    def on_cache_selected(self):
        """Handle cache selection change"""
        selected_items = self.cache_table.selectedItems()
        if not selected_items:
            self.use_button.setEnabled(False)
            self.purge_button.setEnabled(False)
            return

        self.use_button.setEnabled(True)
        self.purge_button.setEnabled(True)

        # Get selected row
        row = selected_items[0].row()

        # Get cache path
        cache_path_item = self.cache_table.item(row, 0)
        if cache_path_item:
             cache_path = cache_path_item.data(Qt.UserRole)
             # Update status
             self.status_label.setText(f"Selected: {Path(cache_path).name}")
        else:
             self.status_label.setText("Selection error.")


    def purge_selected_cache(self):
        """Purge the selected cache"""
        selected_items = self.cache_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a cache to purge.")
            return

        # Get selected row
        row = selected_items[0].row()

        # Get cache path
        cache_path_item = self.cache_table.item(row, 0)
        if not cache_path_item:
             QMessageBox.critical(self, "Error", "Could not get cache path from selection.")
             return
        cache_path = cache_path_item.data(Qt.UserRole)
        cache_name = Path(cache_path).name

        reply = QMessageBox.question(self, 'Confirm Purge',
                                     f"Are you sure you want to delete the cache file '{cache_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            logging.info(f"User confirmed purging cache: {cache_path}")
            # Purge cache - CacheManager will emit signals handled by on_cache_purged and refresh_caches
            success = self.cache_manager.purge_cache(cache_path)
            # Status update is handled by on_cache_purged
        else:
             logging.info("User cancelled purging selected cache.")


    def use_selected_cache(self):
        """Use the selected cache"""
        selected_items = self.cache_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a cache to use.")
            return

        # Get selected row
        row = selected_items[0].row()

        # Get cache path
        cache_path_item = self.cache_table.item(row, 0)
        if not cache_path_item:
             QMessageBox.critical(self, "Error", "Could not get cache path from selection.")
             return
        cache_path = cache_path_item.data(Qt.UserRole)

        # Emit signal
        self.cache_selected.emit(cache_path)

        # Update status
        self.status_label.setText(f"Using cache: {Path(cache_path).name}")

    def on_cache_purged(self, cache_path, success):
        """Handle cache purged signal"""
        # This signal comes from CacheManager after a single purge
        if success:
             # No need to call refresh_caches here, as CacheManager emits cache_list_updated
             # which is already connected to refresh_caches.
             self.cache_purged.emit() # Emit our own signal if needed elsewhere
             self.status_label.setText(f"Cache purged: {Path(cache_path).name}")
        else:
             QMessageBox.warning(self, "Purge Error", f"Failed to purge cache: {Path(cache_path).name}")

    def confirm_purge_all_caches(self):
        """Show confirmation dialog before purging all caches."""
        reply = QMessageBox.question(self, 'Confirm Purge All',
                                     "Are you sure you want to delete ALL .llama_cache files in the cache directory? This cannot be undone.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            logging.info("User confirmed purging all caches.")
            self.status_label.setText("Purging all caches...")
            QApplication.processEvents() # Update UI immediately
            try:
                success = self.cache_manager.purge_all_caches()
                if success:
                    self.status_label.setText("All caches purged.")
                    # CacheManager's purge_all_caches should emit cache_list_updated, triggering refresh
                else:
                    self.status_label.setText("Some caches failed to purge.")
                    QMessageBox.warning(self, "Purge Error", "Failed to purge one or more cache files. Check logs.")
            except Exception as e:
                 logging.error(f"Error during purge all operation: {e}")
                 QMessageBox.critical(self, "Purge Error", f"An unexpected error occurred: {e}")
                 self.status_label.setText("Error purging caches.")
        else:
            logging.info("User cancelled purging all caches.")
            self.status_label.setText("Purge all cancelled.")
