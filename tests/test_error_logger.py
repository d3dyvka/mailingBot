"""
Unit tests for ErrorLogger.

Tests error logging functionality, format, and context handling.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
from utils.error_logger import ErrorLogger


class TestErrorLogger:
    """Test suite for ErrorLogger class."""
    
    def setup_method(self):
        """Set up test fixtures with temporary directory."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.logger = ErrorLogger(log_dir=self.test_dir)
    
    def teardown_method(self):
        """Clean up test directory."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test ErrorLogger initialization."""
        assert self.logger.log_file.exists()
        assert self.logger.log_file.name == "errors.txt"
        assert self.logger.error_count == 0
    
    def test_log_error_basic(self):
        """Test basic error logging."""
        self.logger.log_error("TestError", "This is a test error")
        
        assert self.logger.error_count == 1
        
        log_content = self.logger.read_log()
        assert "TestError" in log_content
        assert "This is a test error" in log_content
        assert "Message:" in log_content
        assert "---" in log_content
    
    def test_log_error_with_context(self):
        """Test error logging with context."""
        context = {
            "user_id": 12345,
            "group": "https://t.me/testgroup",
            "batch": 2
        }
        
        self.logger.log_error("ContextError", "Error with context", context)
        
        assert self.logger.error_count == 1
        
        log_content = self.logger.read_log()
        assert "ContextError" in log_content
        assert "Error with context" in log_content
        assert "Context:" in log_content
        assert "12345" in log_content
        assert "testgroup" in log_content
    
    def test_log_error_timestamp(self):
        """Test that error logging includes timestamp."""
        self.logger.log_error("TimestampTest", "Testing timestamp")
        
        log_content = self.logger.read_log()
        # Check for timestamp format [YYYY-MM-DD HH:MM:SS]
        assert "[" in log_content
        assert "]" in log_content
        # Check that current year is in the log
        current_year = str(datetime.now().year)
        assert current_year in log_content
    
    def test_log_telegram_error_basic(self):
        """Test Telegram error logging without user ID."""
        error = ValueError("Test telegram error")
        
        self.logger.log_telegram_error(error)
        
        assert self.logger.error_count == 1
        
        log_content = self.logger.read_log()
        assert "ValueError" in log_content
        assert "Test telegram error" in log_content
        assert "Message:" in log_content
    
    def test_log_telegram_error_with_user_id(self):
        """Test Telegram error logging with user ID."""
        error = RuntimeError("User-specific error")
        user_id = 98765
        
        self.logger.log_telegram_error(error, user_id=user_id)
        
        assert self.logger.error_count == 1
        
        log_content = self.logger.read_log()
        assert "RuntimeError" in log_content
        assert "User ID: 98765" in log_content
        assert "User-specific error" in log_content
    
    def test_log_telegram_error_with_context(self):
        """Test Telegram error logging with context."""
        error = Exception("Error with context")
        context = {"batch": 3, "attempt": 2}
        
        self.logger.log_telegram_error(error, user_id=12345, context=context)
        
        log_content = self.logger.read_log()
        assert "Exception" in log_content
        assert "User ID: 12345" in log_content
        assert "Context:" in log_content
        assert "batch" in log_content
        assert "attempt" in log_content
    
    def test_log_telegram_error_with_seconds_attribute(self):
        """Test Telegram error logging with FloodWait-like error."""
        # Create a mock FloodWait error with seconds attribute
        class MockFloodWaitError(Exception):
            def __init__(self, message, seconds):
                super().__init__(message)
                self.seconds = seconds
        
        error = MockFloodWaitError("Flood wait", 3600)
        
        self.logger.log_telegram_error(error, user_id=11111)
        
        log_content = self.logger.read_log()
        assert "MockFloodWaitError" in log_content
        assert "Wait time: 3600 seconds" in log_content
        assert "User ID: 11111" in log_content
    
    def test_multiple_errors(self):
        """Test logging multiple errors."""
        self.logger.log_error("Error1", "First error")
        self.logger.log_error("Error2", "Second error")
        self.logger.log_telegram_error(ValueError("Third error"), user_id=123)
        
        assert self.logger.error_count == 3
        
        log_content = self.logger.read_log()
        assert "Error1" in log_content
        assert "Error2" in log_content
        assert "ValueError" in log_content
        assert "First error" in log_content
        assert "Second error" in log_content
        assert "Third error" in log_content
    
    def test_get_error_count(self):
        """Test error count tracking."""
        assert self.logger.get_error_count() == 0
        
        self.logger.log_error("Test1", "Error 1")
        assert self.logger.get_error_count() == 1
        
        self.logger.log_error("Test2", "Error 2")
        assert self.logger.get_error_count() == 2
        
        self.logger.log_telegram_error(Exception("Test3"))
        assert self.logger.get_error_count() == 3
    
    def test_clear_log(self):
        """Test clearing the error log."""
        self.logger.log_error("Test", "Test error")
        assert self.logger.error_count == 1
        assert len(self.logger.read_log()) > 0
        
        self.logger.clear_log()
        
        assert self.logger.error_count == 0
        assert self.logger.read_log() == ""
    
    def test_get_log_path(self):
        """Test getting log file path."""
        log_path = self.logger.get_log_path()
        
        assert isinstance(log_path, Path)
        assert log_path.name == "errors.txt"
        assert log_path.exists()
    
    def test_read_log_empty(self):
        """Test reading empty log."""
        content = self.logger.read_log()
        assert content == ""
    
    def test_read_log_with_content(self):
        """Test reading log with content."""
        self.logger.log_error("ReadTest", "Testing read")
        
        content = self.logger.read_log()
        assert len(content) > 0
        assert "ReadTest" in content
        assert "Testing read" in content
    
    def test_log_file_persistence(self):
        """Test that log file persists across logger instances."""
        self.logger.log_error("Persistent", "First logger")
        
        # Create new logger instance with same directory
        logger2 = ErrorLogger(log_dir=self.test_dir)
        logger2.log_error("Persistent2", "Second logger")
        
        # Both errors should be in the log
        content = logger2.read_log()
        assert "First logger" in content
        assert "Second logger" in content
    
    def test_log_format_structure(self):
        """Test that log entries follow the correct format."""
        self.logger.log_error("FormatTest", "Testing format", {"key": "value"})
        
        log_content = self.logger.read_log()
        lines = log_content.strip().split('\n')
        
        # Check structure
        assert lines[0].startswith('[')  # Timestamp line
        assert "FormatTest" in lines[0]
        assert lines[1].startswith('Message:')
        assert lines[2].startswith('Context:')
        assert lines[3] == '---'
    
    def test_unicode_support(self):
        """Test that logger handles unicode characters."""
        self.logger.log_error("UnicodeTest", "Тестовая ошибка с юникодом 🔥")
        
        log_content = self.logger.read_log()
        assert "Тестовая ошибка с юникодом 🔥" in log_content
    
    def test_special_characters_in_context(self):
        """Test logging with special characters in context."""
        context = {
            "url": "https://t.me/group?invite=abc123",
            "message": "Error: Connection failed!",
            "symbols": "<>&\"'"
        }
        
        self.logger.log_error("SpecialChars", "Testing special chars", context)
        
        log_content = self.logger.read_log()
        assert "https://t.me/group?invite=abc123" in log_content
        assert "Error: Connection failed!" in log_content
    
    def test_empty_context(self):
        """Test logging with empty context dictionary."""
        self.logger.log_error("EmptyContext", "Error message", {})
        
        log_content = self.logger.read_log()
        assert "EmptyContext" in log_content
        assert "Error message" in log_content
        # Empty context dictionary is falsy, so it won't be logged
        assert "Context:" not in log_content
    
    def test_none_context(self):
        """Test logging with None context."""
        self.logger.log_error("NoneContext", "Error message", None)
        
        log_content = self.logger.read_log()
        assert "NoneContext" in log_content
        assert "Error message" in log_content
        # None context should not appear in log
        assert "Context:" not in log_content
    
    def test_error_count_after_clear(self):
        """Test that error count resets after clearing log."""
        self.logger.log_error("Test1", "Error 1")
        self.logger.log_error("Test2", "Error 2")
        assert self.logger.error_count == 2
        
        self.logger.clear_log()
        assert self.logger.error_count == 0
        
        self.logger.log_error("Test3", "Error 3")
        assert self.logger.error_count == 1
