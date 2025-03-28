#!/usr/bin/env python3
"""
Welcome dialog for LlamaCag UI shown on first launch.
"""
import sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QCheckBox, QPushButton, QDialogButtonBox,
    QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QSettings

class WelcomeDialog(QDialog):
    """
    A dialog window shown on the first launch of the application
    to guide the user through the initial setup and core concepts.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("LlamaCag", "LlamaCagUI")
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface for the dialog."""
        self.setWindowTitle("Welcome to LlamaCag UI!")
        self.setMinimumSize(600, 500) # Adjusted size for content

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- Title ---
        title_label = QLabel("👋 Welcome to LlamaCag UI!")
        title_font = self.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # --- Introduction ---
        intro_text = """
        <p>Hi there! LlamaCag UI lets you 'chat' with your documents using Large Language Models (LLMs), leveraging their full context window for high accuracy.</p>
        <p><b>Key Concept: Context-Augmented Generation (CAG) & Strict Answering</b></p>
        <p>Instead of retrieving snippets (like RAG), LlamaCag processes the <i>entire</i> document through the selected LLM once to create a <b>KV Cache</b> (the model's 'memory' of the document). When you chat, this cache is loaded, allowing fast, context-aware answers based <i>only</i> on the document's content. The model is prevented from using outside knowledge or hallucinating.</p>
        """
        intro_label = QLabel(intro_text)
        intro_label.setWordWrap(True)
        intro_label.setTextFormat(Qt.RichText)
        intro_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(intro_label)

        # --- Step-by-Step Guide ---
        guide_title = QLabel("🚀 Getting Started: First-Time Setup")
        guide_font = self.font()
        guide_font.setPointSize(13)
        guide_font.setBold(True)
        guide_title.setFont(guide_font)
        layout.addWidget(guide_title)

        guide_text = """
        <ol>
            <li><b>Download/Select a Model:</b> Go to the '<b>Models</b>' tab. Download a model (e.g., Gemma 3 4B Q4_K_M for a good balance of speed and capability) or import one (GGUF format). <b>Select the model you want to use for processing and chatting.</b></li>

            <li><b>Process Your Document:</b> Go to the '<b>Documents</b>' tab. Select your text file (<code>.txt</code>, <code>.md</code>). Click '<b>Create KV Cache</b>'.
                <ul><li>This uses the <i>currently selected model</i> to read the document and save its KV Cache.</li>
                    <li>Processing large documents (e.g., 128k tokens) can take time, especially without GPU acceleration (see Settings below).</li>
                    <li>Optionally check '<b>Set as Master KV Cache</b>' to make this the default cache used by the Chat tab if no other cache is explicitly selected.</li>
                </ul>
            </li>

            <li><b>Load Context & Chat:</b> Go to the '<b>Chat</b>' tab and ensure '<b>Use KV Cache</b>' is checked.
                <ul><li><b>Method A (Specific Cache):</b> Go to '<b>KV Cache Monitor</b>', select the cache for your document, click '<b>Use Selected</b>'. This guarantees you're chatting with that specific document's context.</li>
                    <li><b>Method B (Master Cache):</b> If you set a Master Cache and haven't specifically selected another one via the Monitor, the Chat tab will use the Master Cache by default.</li>
                    <li><b>Method C (Warm-Up - Recommended for Performance):</b> After selecting a cache (Method A or B), click the '<b>Warm Up Cache</b>' button in the Chat tab. This pre-loads the model and cache into memory for the fastest possible responses during your chat session.</li>
                </ul>
            </li>

            <li><b>Ask Questions:</b> Type your question and hit Send. The model will answer based *only* on the loaded document context.</li>
        </ol>
        <p><b><font color='red'>VERY IMPORTANT:</font> KV Caches are Model-Specific!</b> A cache created with Model A <u>cannot</u> be used with Model B. You must create a separate cache for each document *using the specific model* you intend to chat with.</p>
        """
        guide_label = QLabel(guide_text)
        guide_label.setWordWrap(True)
        guide_label.setTextFormat(Qt.RichText)
        guide_label.setAlignment(Qt.AlignLeft)
        # Allow links to be opened if any were added (none currently)
        guide_label.setOpenExternalLinks(True)
        layout.addWidget(guide_label)

        # --- Performance Settings (macOS M4 Pro Focus) ---
        perf_title = QLabel("⚙️ Performance Settings (Especially for Mac)")
        perf_title.setFont(guide_font) # Reuse guide font
        layout.addWidget(perf_title)

        perf_text = """
        <p>Processing large documents requires significant computation. Go to the '<b>Settings</b>' tab to optimize:</p>
        <ul>
            <li><b>GPU Layers:</b> <font color='orange'><b>This is crucial for speed on Apple Silicon (like your M4 Pro)!</b></font> It determines how many model layers run on the GPU (Metal). Start with <b>15-20</b> for 4B models or <b>10-15</b> for 8B models on 24GB RAM. Increase cautiously while monitoring memory in Activity Monitor. Too high uses too much RAM and slows down; 0 uses CPU only (slow).</li>
            <li><b>CPU Cores (Threads):</b> Set to your number of <i>performance</i> cores (e.g., 8 or 10 for M4 Pro).</li>
            <li><b>Batch Size:</b> Tokens processed in parallel during cache creation. Default 512 is usually fine. Lower to 256 if RAM usage is too high during processing.</li>
        </ul>
        <p><i>Note: Even with GPU offload, 128k token processing takes time. Some slowdown might also be due to `llama.cpp`'s Metal backend optimizations. Remember to Save Settings and restart the app after changes.</i></p>
        """
        perf_label = QLabel(perf_text)
        perf_label.setWordWrap(True)
        perf_label.setTextFormat(Qt.RichText)
        perf_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(perf_label)


        # --- Spacer ---
        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)) # Reduced spacer

        # --- Don't Show Again Checkbox ---
        self.dont_show_checkbox = QCheckBox("Don't show this message again")
        layout.addWidget(self.dont_show_checkbox)

        # --- Buttons ---
        button_box = QDialogButtonBox()
        close_button = button_box.addButton("Close", QDialogButtonBox.AcceptRole)
        layout.addWidget(button_box)

        # Connect signals
        close_button.clicked.connect(self.accept) # Use accept to handle closing

    def accept(self):
        """Handle dialog acceptance (Close button clicked)."""
        if self.dont_show_checkbox.isChecked():
            self.settings.setValue("showWelcomeDialog", False)
        else:
            # Ensure the setting is True if the box is unchecked when closing
            self.settings.setValue("showWelcomeDialog", True)
        super().accept()

    @staticmethod
    def should_show(default=True):
        """Check QSettings to see if the dialog should be shown."""
        settings = QSettings("LlamaCag", "LlamaCagUI")
        return settings.value("showWelcomeDialog", defaultValue=default, type=bool)

# Example usage for testing (optional)
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    # To test persistence, uncomment the next line to reset the setting
    # QSettings("LlamaCag", "LlamaCagUI").setValue("showWelcomeDialog", True)
    if WelcomeDialog.should_show():
        dialog = WelcomeDialog()
        dialog.exec_() # Use exec_ for modal testing
    else:
        print("Welcome dialog is set to not show.")
    sys.exit()
