#!/usr/bin/env python3
"""
Toast notification component for LlamaCag UI
Provides pop-up notifications that automatically disappear after a timeout.
"""
import os
import sys
from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout,
    QPushButton, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor
class Toast(QWidget):
    """Toast notification widget that fades in and out"""
    def __init__(self, parent: QWidget, message: str, timeout: int = 3000,
                 color: str = "#323232"):
        """
        Initialize toast notification
        Args:
            parent: Parent widget
            message: Message to display
            timeout: Time in ms before the toast disappears (default: 3000ms)
            color: Background color (default: dark gray)
        """
        super().__init__(parent)
        # Store parameters
        self.message = message
        self.timeout = timeout
        # Set up widget properties
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        # Create message label
        self.label = QLabel(message)
        self.label.setStyleSheet("color: white;")
        layout.addWidget(self.label)
        # Optional close button
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(20, 20)
        self.close_button.setStyleSheet(
            "QPushButton { color: white; border: none; font-size: 16px; } "
            "QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }"
        )
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button)
        # Set background color
        self.setStyleSheet(f"background-color: {color}; border-radius: 10px;")
        # Set up fade effect
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self.opacity_effect)
        # Position at bottom of parent
        self._reposition()
    def _reposition(self):
        """Position the toast at the bottom of the parent"""
        parent_rect = self.parent().rect()
        self_size = self.sizeHint()
        x = parent_rect.width() // 2 - self_size.width() // 2
        y = parent_rect.height() - self_size.height() - 50  # 50px from bottom
        self.setGeometry(x, y, self_size.width(), self_size.height())
    def show(self):
        """Show the toast with fade-in animation"""
        super().show()
        # Fade in animation
        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(250)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_in_animation.start()
        # Start timer for automatic close
        QTimer.singleShot(self.timeout, self.start_fade_out)
    def start_fade_out(self):
        """Start fade out animation"""
        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(250)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_out_animation.finished.connect(self.close)
        self.fade_out_animation.start()