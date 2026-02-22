"""
Error Logger for Telegram Mailer MacOS App.

Automatically logs all errors to errors.txt with full context including
error type, timestamp, context, and user ID.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import traceback

from .constants import LOG_DIR, ERROR_LOG_FILE


class ErrorLogger:
    """
    Automatic error logging to errors.txt.
    
    Logs all errors with complete context including error type, timestamp,
    context information, and user ID (when applicable). Supports both
    general errors and Telegram-specific errors.
    
    Attributes:
        log_file: Path to the errors.txt file
        error_count: Number of errors logged in current session
    """
    
    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize the error logger.
        
        Args:
            log_dir: Directory for log files (defaults to LOG_DIR constant)
        """
        if log_dir is None:
            log_dir = LOG_DIR
        
        # Ensure log directory exists
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = log_dir / ERROR_LOG_FILE
        self.error_count = 0
        
        # Create log file if it doesn't exist
        if not self.log_file.exists():
            self.log_file.touch()
    
    def log_error(
        self,
        error_type: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an error with full context.
        
        Format:
        [YYYY-MM-DD HH:MM:SS] ErrorType
        Message: error message
        Context: {context_dict}
        ---
        
        Args:
            error_type: Type/name of the error
            message: Error message description
            context: Additional context information (optional)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = f"[{timestamp}] {error_type}\n"
        log_entry += f"Message: {message}\n"
        
        if context:
            log_entry += f"Context: {context}\n"
        
        log_entry += "---\n"
        
        # Append to log file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        self.error_count += 1
    
    def log_telegram_error(
        self,
        error: Exception,
        user_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Specialized logging for Telegram API errors.
        
        Automatically extracts error type and formats Telegram-specific
        information like FloodWait duration, user privacy settings, etc.
        
        Format:
        [YYYY-MM-DD HH:MM:SS] TelegramErrorType
        User ID: user_id (if provided)
        Message: error message
        Context: {context_dict}
        Traceback: (if available)
        ---
        
        Args:
            error: The exception that occurred
            user_id: Telegram user ID (optional)
            context: Additional context information (optional)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_type = type(error).__name__
        
        log_entry = f"[{timestamp}] {error_type}\n"
        
        if user_id is not None:
            log_entry += f"User ID: {user_id}\n"
        
        # Extract error message
        error_message = str(error)
        log_entry += f"Message: {error_message}\n"
        
        # Handle specific Telegram error types
        if hasattr(error, 'seconds'):
            # FloodWaitError has a 'seconds' attribute
            log_entry += f"Wait time: {error.seconds} seconds\n"
        
        if context:
            log_entry += f"Context: {context}\n"
        
        # Add traceback for debugging
        tb = traceback.format_exc()
        if tb and tb != "NoneType: None\n":
            log_entry += f"Traceback:\n{tb}\n"
        
        log_entry += "---\n"
        
        # Append to log file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        self.error_count += 1
    
    def get_error_count(self) -> int:
        """
        Get the number of errors logged in the current session.
        
        Returns:
            int: Number of errors logged since initialization
        """
        return self.error_count
    
    def clear_log(self) -> None:
        """
        Clear the error log file.
        
        Warning: This permanently deletes all logged errors.
        """
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("")
        
        self.error_count = 0
    
    def get_log_path(self) -> Path:
        """
        Get the path to the error log file.
        
        Returns:
            Path: Path to errors.txt
        """
        return self.log_file
    
    def read_log(self) -> str:
        """
        Read the entire error log.
        
        Returns:
            str: Contents of the error log file
        """
        if not self.log_file.exists():
            return ""
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            return f.read()
