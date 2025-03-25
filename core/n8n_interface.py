#!/usr/bin/env python3
"""
n8n interface for LlamaCag UI
Provides connectivity with n8n services.
"""
import os
import sys
import logging
import requests
import json
import subprocess
import time
import threading
from typing import Dict, List, Optional
from PyQt5.QtCore import QObject, pyqtSignal
class N8nInterface(QObject):
    """Interface for communicating with n8n"""
    # Signals
    status_changed = pyqtSignal(bool)  # is_running
    def __init__(self, config):
        """Initialize n8n interface"""
        super().__init__()
        self.config = config
        self.n8n_url = f"{config.get('N8N_PROTOCOL', 'http')}://{config.get('N8N_HOST', 'localhost')}:{config.get('N8N_PORT', '5678')}"
        # Start status checking thread
        self._running = True
        self._status_thread = threading.Thread(target=self._check_status_thread, daemon=True)
        self._status_thread.start()
    def _check_status_thread(self):
        """Thread for checking n8n status"""
        last_status = None
        while self._running:
            current_status = self.is_running()
            if current_status != last_status:
                self.status_changed.emit(current_status)
                last_status = current_status
            time.sleep(10)  # Check every 10 seconds
    def is_running(self) -> bool:
        """Check if n8n is running"""
        try:
            response = requests.get(f"{self.n8n_url}/healthz", timeout=2)
            return response.status_code == 200
        except Exception:
            return False
    def start_services(self) -> bool:
        """Start n8n services"""
        try:
            # Run docker-compose up -d
            subprocess.run(
                "cd ~/llama-cag-n8n && docker compose up -d",
                shell=True, check=True
            )
            return True
        except Exception as e:
            logging.error(f"Failed to start n8n services: {str(e)}")
            return False
    def stop_services(self) -> bool:
        """Stop n8n services"""
        try:
            # Run docker-compose down
            subprocess.run(
                "cd ~/llama-cag-n8n && docker compose down",
                shell=True, check=True
            )
            return True
        except Exception as e:
            logging.error(f"Failed to stop n8n services: {str(e)}")
            return False
    def submit_document(self, document_path: str) -> bool:
        """Submit a document to n8n for processing"""
        try:
            # Call webhook
            response = requests.post(
                f"{self.n8n_url}/webhook/document-processing",
                json={
                    "documentPath": document_path,
                    "documentId": os.path.basename(document_path)
                }
            )
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Failed to submit document to n8n: {str(e)}")
            return False
    def query_document(self, query: str, max_tokens: int = 1024) -> Optional[str]:
        """Query documents via n8n"""
        try:
            # Call webhook
            response = requests.post(
                f"{self.n8n_url}/webhook/cag/query",
                json={
                    "query": query,
                    "maxTokens": max_tokens
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                return None
        except Exception as e:
            logging.error(f"Failed to query via n8n: {str(e)}")
            return None
    def update_config(self, config):
        """Update configuration"""
        self.config = config
        new_n8n_url = f"{config.get('N8N_PROTOCOL', 'http')}://{config.get('N8N_HOST', 'localhost')}:{config.get('N8N_PORT', '5678')}"
        if new_n8n_url != self.n8n_url:
            self.n8n_url = new_n8n_url