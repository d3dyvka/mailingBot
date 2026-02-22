#!/usr/bin/env python3
"""
Test script for text editor panel improvements.
Tests dynamic resizing, color selection, and button placement.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from ui.text_editor_panel import TextEditorPanel


class TestWindow(QMainWindow):
    """Test window for text editor panel."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тест редактора текста")
        self.setMinimumSize(800, 600)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Layout
        layout = QVBoxLayout(central)
        
        # Add text editor panel
        self.editor = TextEditorPanel()
        self.editor.message_saved.connect(self.on_message_saved)
        layout.addWidget(self.editor)
        
        print("✓ Редактор создан")
        print("✓ Проверьте:")
        print("  1. Кнопка 'Сохранить' находится ПОД текстовым полем")
        print("  2. При вводе текста поле расширяется")
        print("  3. Есть кнопка 'Цвет текста' в панели инструментов")
        print("  4. Scrollbar появляется при большом количестве текста")
    
    def on_message_saved(self, html, plain):
        print(f"\n✓ Сообщение сохранено!")
        print(f"  HTML: {html[:100]}...")
        print(f"  Plain: {plain[:100]}...")


def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
