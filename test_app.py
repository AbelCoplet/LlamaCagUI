#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget
class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LlamaCag Test App")
        self.setGeometry(100, 100, 400, 200)
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        # Create layout
        layout = QVBoxLayout(central)
        # Add some widgets
        label = QLabel("LlamaCag Test Application")
        layout.addWidget(label)
        button = QPushButton("Click Me")
        button.clicked.connect(lambda: label.setText("Button clicked!"))
        layout.addWidget(button)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())