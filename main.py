#!/usr/bin/env python3
"""
Telegram Mailer - GUI Application
Main entry point for the PyQt6 GUI application
"""

import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow
from utils.constants import ensure_app_directories


def exception_hook(exctype, value, tb):
    """Global exception handler to catch unhandled exceptions."""
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    print(f"Unhandled exception:\n{error_msg}")
    
    # Save to crash log
    try:
        from pathlib import Path
        from datetime import datetime
        from utils.constants import LOG_DIR
        
        crash_log = LOG_DIR / "crash.log"
        with open(crash_log, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Crash at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*80}\n")
            f.write(error_msg)
            f.write(f"\n{'='*80}\n\n")
    except Exception as e:
        print(f"Failed to write crash log: {e}")
    
    # Try to show error dialog
    try:
        QMessageBox.critical(
            None,
            "Критическая ошибка",
            f"Произошла непредвиденная ошибка:\n\n{str(value)}\n\n"
            f"Приложение будет закрыто.\n"
            f"Лог ошибки сохранен в crash.log"
        )
    except:
        pass
    
    sys.exit(1)


def main():
    """Launch the GUI application"""
    # Set global exception handler
    sys.excepthook = exception_hook
    
    # Ensure all required directories exist
    ensure_app_directories()
    
    app = QApplication(sys.argv)
    app.setApplicationName("Telegram Mailer")
    app.setOrganizationName("TelegramMailer")
    
    try:
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error starting application: {e}")
        traceback.print_exc()
        QMessageBox.critical(
            None,
            "Ошибка запуска",
            f"Не удалось запустить приложение:\n{str(e)}"
        )
        sys.exit(1)


if __name__ == '__main__':
    main()
