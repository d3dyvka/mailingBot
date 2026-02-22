"""
Demo for Text Editor Panel and Progress Panel.

This demo shows how to use the TextEditorPanel and ProgressPanel
components independently or together.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QGroupBox
from ui.text_editor_panel import TextEditorPanel
from ui.progress_panel import ProgressPanel


class DemoWindow(QMainWindow):
    """Demo window showing text editor and progress panels."""
    
    def __init__(self):
        """Initialize the demo window."""
        super().__init__()
        
        self.setWindowTitle("Text Editor & Progress Panel Demo")
        self.setMinimumSize(800, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Text Editor Panel
        editor_group = QGroupBox("Message Editor")
        editor_layout = QVBoxLayout()
        self.text_editor = TextEditorPanel()
        self.text_editor.message_saved.connect(self.on_message_saved)
        editor_layout.addWidget(self.text_editor)
        editor_group.setLayout(editor_layout)
        layout.addWidget(editor_group)
        
        # Progress Panel
        self.progress_panel = ProgressPanel()
        self.progress_panel.reset_progress_clicked.connect(self.on_reset_progress)
        self.progress_panel.logout_clicked.connect(self.on_logout)
        layout.addWidget(self.progress_panel)
        
        # Initialize with demo data
        self.setup_demo_data()
        
        # Status bar
        self.statusBar().showMessage("Ready - Try editing a message and saving it!")
    
    def setup_demo_data(self):
        """Setup demo data for the panels."""
        # Set some sample text in the editor
        sample_html = """
        <p>Welcome to the <b>Telegram Mailer</b> demo!</p>
        <p>You can use <i>formatting</i> like <u>underline</u> and <a href="https://example.com">links</a>.</p>
        <p>Try the emoji picker too! 😀</p>
        """
        self.text_editor.set_content(sample_html)
        
        # Setup progress panel with demo data
        self.progress_panel.set_total_users(100)
        self.progress_panel.update_progress(sent=30, failed=5)
        
        # Start a demo countdown (5 minutes)
        self.progress_panel.start_countdown(300, "Demo countdown - 5 minutes")
    
    def on_message_saved(self, html_content: str, plain_text: str):
        """Handle message saved event."""
        print("\n=== Message Saved ===")
        print(f"Plain Text:\n{plain_text}\n")
        print(f"HTML Content:\n{html_content}\n")
        
        self.statusBar().showMessage("Message saved! Check console for output.")
    
    def on_reset_progress(self):
        """Handle reset progress event."""
        print("\n=== Progress Reset ===")
        self.progress_panel.reset_progress()
        self.statusBar().showMessage("Progress reset!")
    
    def on_logout(self):
        """Handle logout event."""
        print("\n=== Logout Clicked ===")
        self.statusBar().showMessage("Logout clicked!")


def main():
    """Main entry point for the demo."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    window = DemoWindow()
    window.show()
    
    print("=" * 60)
    print("Text Editor & Progress Panel Demo")
    print("=" * 60)
    print("\nFeatures to try:")
    print("1. Edit the message in the text editor")
    print("2. Use formatting buttons (Bold, Italic, Underline)")
    print("3. Insert links and emojis")
    print("4. Click 'Save Message' to see HTML output in console")
    print("5. Watch the countdown timer")
    print("6. Try the Reset Progress and Logout buttons")
    print("\nThe progress panel shows:")
    print("- Sent: 30 messages")
    print("- Failed: 5 messages")
    print("- Remaining: 65 messages")
    print("- Total: 100 messages")
    print("=" * 60)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
