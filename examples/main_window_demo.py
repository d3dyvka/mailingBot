#!/usr/bin/env python3
"""
Demo script for Main Window GUI.

This script demonstrates the main window with all panels:
- Configuration panel for API credentials
- Authentication panel for Telegram login
- Group selection panel
- End date panel with delay calculation

Run this script to see the GUI in action.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    """Run the main window demo."""
    print("Starting Telegram Mailer Main Window Demo...")
    print("\nFeatures:")
    print("1. Configuration Panel - Enter and save API credentials")
    print("2. Authentication Panel - Login to Telegram")
    print("3. Group Selection - Load group members")
    print("4. End Date Panel - Calculate optimal delays")
    print("\nNote: This is a demo. You'll need valid Telegram API credentials to test authentication.")
    print("\nClosing the window will save its geometry for next time.")
    print("-" * 60)
    
    # Create application
    app = QApplication(sys.argv)
    
    # Set application style for MacOS
    app.setStyle("Fusion")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Connect signals for demo
    window.credentials_saved.connect(
        lambda api_id, api_hash: print(f"\n✓ Credentials saved: API_ID={api_id}")
    )
    window.authenticated.connect(
        lambda: print("\n✓ Authentication successful!")
    )
    window.group_selected.connect(
        lambda count: print(f"\n✓ Group loaded: {count} members")
    )
    
    print("\nWindow opened. Interact with the GUI to test features.")
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
