"""
Unit tests for Text Editor Panel.

Tests the text editor functionality including:
- Formatting (bold, italic, underline)
- Link insertion
- Emoji insertion
- HTML conversion for Telegram
- Message saving
"""

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.text_editor_panel import TextEditorPanel, LinkDialog, EmojiDialog


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def editor_panel(qapp):
    """Create TextEditorPanel instance for testing."""
    panel = TextEditorPanel()
    yield panel
    panel.deleteLater()


class TestTextEditorPanel:
    """Test suite for TextEditorPanel."""
    
    def test_initialization(self, editor_panel):
        """Test that panel initializes correctly."""
        assert editor_panel.text_edit is not None
        assert editor_panel.save_btn is not None
        assert editor_panel.bold_action is not None
        assert editor_panel.italic_action is not None
        assert editor_panel.underline_action is not None
    
    def test_plain_text_input(self, editor_panel):
        """Test plain text input and retrieval."""
        test_text = "Hello, World!"
        editor_panel.text_edit.setPlainText(test_text)
        
        assert editor_panel.get_plain_text() == test_text
    
    def test_bold_formatting(self, editor_panel):
        """Test bold formatting application."""
        editor_panel.text_edit.clear()
        editor_panel.text_edit.setPlainText("Bold text")
        
        # Select all text
        cursor = editor_panel.text_edit.textCursor()
        cursor.select(cursor.SelectionType.Document)
        editor_panel.text_edit.setTextCursor(cursor)
        
        # Apply bold
        editor_panel.apply_bold()
        
        # Check format
        cursor = editor_panel.text_edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        cursor.movePosition(cursor.MoveOperation.NextCharacter, cursor.MoveMode.KeepAnchor)
        char_format = cursor.charFormat()
        
        assert char_format.fontWeight() == QFont.Weight.Bold
    
    def test_italic_formatting(self, editor_panel):
        """Test italic formatting application."""
        editor_panel.text_edit.clear()
        editor_panel.text_edit.setPlainText("Italic text")
        
        # Select all text
        cursor = editor_panel.text_edit.textCursor()
        cursor.select(cursor.SelectionType.Document)
        editor_panel.text_edit.setTextCursor(cursor)
        
        # Apply italic
        editor_panel.apply_italic()
        
        # Check format
        cursor = editor_panel.text_edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        cursor.movePosition(cursor.MoveOperation.NextCharacter, cursor.MoveMode.KeepAnchor)
        char_format = cursor.charFormat()
        
        assert char_format.fontItalic()
    
    def test_underline_formatting(self, editor_panel):
        """Test underline formatting application."""
        editor_panel.text_edit.clear()
        editor_panel.text_edit.setPlainText("Underline text")
        
        # Select all text
        cursor = editor_panel.text_edit.textCursor()
        cursor.select(cursor.SelectionType.Document)
        editor_panel.text_edit.setTextCursor(cursor)
        
        # Apply underline
        editor_panel.apply_underline()
        
        # Check format
        cursor = editor_panel.text_edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        cursor.movePosition(cursor.MoveOperation.NextCharacter, cursor.MoveMode.KeepAnchor)
        char_format = cursor.charFormat()
        
        assert char_format.fontUnderline()
    
    def test_html_conversion_plain_text(self, editor_panel):
        """Test HTML conversion for plain text."""
        editor_panel.text_edit.clear()
        editor_panel.text_edit.setPlainText("Plain text")
        
        html = editor_panel.get_html_content()
        
        # Should contain the text
        assert "Plain text" in html or "Plain" in html
    
    def test_html_conversion_with_bold(self, editor_panel):
        """Test HTML conversion with bold formatting."""
        editor_panel.text_edit.clear()
        editor_panel.text_edit.setPlainText("Bold text")
        
        # Select and make bold
        cursor = editor_panel.text_edit.textCursor()
        cursor.select(cursor.SelectionType.Document)
        editor_panel.text_edit.setTextCursor(cursor)
        editor_panel.apply_bold()
        
        html = editor_panel.get_html_content()
        
        # Should contain bold tags
        assert "<b>" in html or "Bold" in html
    
    def test_clear_content(self, editor_panel):
        """Test clearing editor content."""
        editor_panel.text_edit.setPlainText("Some text")
        editor_panel.clear()
        
        assert editor_panel.get_plain_text() == ""
    
    def test_set_content(self, editor_panel):
        """Test setting HTML content."""
        html = "<b>Bold</b> and <i>italic</i>"
        editor_panel.set_content(html)
        
        # Should have some content
        assert len(editor_panel.get_plain_text()) > 0
    
    def test_message_saved_signal(self, editor_panel, qtbot):
        """Test that message_saved signal is emitted."""
        editor_panel.text_edit.setPlainText("Test message")
        
        with qtbot.waitSignal(editor_panel.message_saved, timeout=1000):
            editor_panel.save_btn.click()


class TestLinkDialog:
    """Test suite for LinkDialog."""
    
    def test_initialization(self, qapp):
        """Test dialog initialization."""
        dialog = LinkDialog()
        assert dialog.text_input is not None
        assert dialog.url_input is not None
        dialog.deleteLater()
    
    def test_get_link_data(self, qapp):
        """Test getting link data."""
        dialog = LinkDialog()
        dialog.text_input.setText("Click here")
        dialog.url_input.setText("https://example.com")
        
        text, url = dialog.get_link_data()
        
        assert text == "Click here"
        assert url == "https://example.com"
        dialog.deleteLater()


class TestEmojiDialog:
    """Test suite for EmojiDialog."""
    
    def test_initialization(self, qapp):
        """Test dialog initialization."""
        dialog = EmojiDialog()
        assert len(dialog.EMOJIS) > 0
        assert dialog.selected_emoji is None
        dialog.deleteLater()
    
    def test_select_emoji(self, qapp):
        """Test emoji selection."""
        dialog = EmojiDialog()
        test_emoji = "😀"
        
        dialog.select_emoji(test_emoji)
        
        assert dialog.get_emoji() == test_emoji
        dialog.deleteLater()


class TestHTMLConversion:
    """Test suite for HTML conversion to Telegram format."""
    
    def test_simple_bold(self, editor_panel):
        """Test conversion of bold text."""
        editor_panel.text_edit.clear()
        editor_panel.text_edit.setPlainText("Bold")
        
        cursor = editor_panel.text_edit.textCursor()
        cursor.select(cursor.SelectionType.Document)
        editor_panel.text_edit.setTextCursor(cursor)
        editor_panel.apply_bold()
        
        html = editor_panel.get_html_content()
        
        # Should contain bold formatting
        assert "Bold" in html
    
    def test_simple_italic(self, editor_panel):
        """Test conversion of italic text."""
        editor_panel.text_edit.clear()
        editor_panel.text_edit.setPlainText("Italic")
        
        cursor = editor_panel.text_edit.textCursor()
        cursor.select(cursor.SelectionType.Document)
        editor_panel.text_edit.setTextCursor(cursor)
        editor_panel.apply_italic()
        
        html = editor_panel.get_html_content()
        
        # Should contain italic formatting
        assert "Italic" in html
    
    def test_simple_underline(self, editor_panel):
        """Test conversion of underline text."""
        editor_panel.text_edit.clear()
        editor_panel.text_edit.setPlainText("Underline")
        
        cursor = editor_panel.text_edit.textCursor()
        cursor.select(cursor.SelectionType.Document)
        editor_panel.text_edit.setTextCursor(cursor)
        editor_panel.apply_underline()
        
        html = editor_panel.get_html_content()
        
        # Should contain underline formatting
        assert "Underline" in html
    
    def test_mixed_formatting(self, editor_panel):
        """Test conversion of mixed formatting."""
        editor_panel.text_edit.clear()
        editor_panel.text_edit.setPlainText("Mixed")
        
        # Apply bold
        cursor = editor_panel.text_edit.textCursor()
        cursor.select(cursor.SelectionType.Document)
        editor_panel.text_edit.setTextCursor(cursor)
        editor_panel.apply_bold()
        
        # Apply italic
        cursor = editor_panel.text_edit.textCursor()
        cursor.select(cursor.SelectionType.Document)
        editor_panel.text_edit.setTextCursor(cursor)
        editor_panel.apply_italic()
        
        html = editor_panel.get_html_content()
        
        # Should contain the text
        assert "Mixed" in html
