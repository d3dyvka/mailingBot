#!/usr/bin/env python3
"""
Test script for authentication dialog.
Run this to test the auth dialog without building the full app.
"""

import sys
from PyQt6.QtWidgets import QApplication

from ui.auth_dialog import AuthDialog
from telegram.telegram_service import TelegramService
from utils.constants import SESSION_DIR

def main():
    """Test the authentication dialog."""
    app = QApplication(sys.argv)
    
    # Create telegram service
    API_ID = "22937843"
    API_HASH = "f059dadbb0d4d4734feb75dd4fdcb4b9"
    telegram_service = TelegramService(API_ID, API_HASH, SESSION_DIR)
    
    # Create and show auth dialog
    dialog = AuthDialog(telegram_service)
    
    def on_success():
        print("✓ Authentication successful!")
    
    dialog.authentication_success.connect(on_success)
    
    result = dialog.exec()
    
    if result:
        print("Dialog accepted - user authenticated")
    else:
        print("Dialog rejected - user cancelled")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
