"""
User interface module for Telegram Mailer MacOS App.

This module contains all PyQt6 GUI components, including:
- Main window
- Authentication dialog
- Text editor panel
- Progress panel
"""

# Don't import here to avoid circular imports with PyInstaller
# Import directly where needed: from ui.main_window import MainWindow

__all__ = ['MainWindow', 'AuthDialog']
