"""
Text Editor Panel for Telegram Mailer MacOS App.

Provides a rich text editor with formatting toolbar for creating messages:
- Bold, Italic, Underline formatting
- Text color selection
- Link insertion
- Emoji picker
- Dynamic height adjustment
- HTML conversion for Telegram API
- Manual save functionality
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QToolBar,
    QDialog,
    QLineEdit,
    QLabel,
    QDialogButtonBox,
    QMessageBox,
    QGridLayout,
    QColorDialog,
    QCheckBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QTextCharFormat, QFont, QTextCursor, QAction, QColor


class LinkDialog(QDialog):
    """Dialog for inserting links."""
    
    def __init__(self, parent=None):
        """Initialize the link dialog."""
        super().__init__(parent)
        self.setWindowTitle("Вставить ссылку")
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Text input
        text_layout = QHBoxLayout()
        text_label = QLabel("Текст:")
        text_label.setMinimumWidth(60)
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Текст ссылки")
        self.text_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                color: black;
                border: 2px solid #e1e8ed;
                border-radius: 6px;
                padding: 6px;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background-color: white;
                color: black;
            }
        """)
        text_layout.addWidget(text_label)
        text_layout.addWidget(self.text_input)
        layout.addLayout(text_layout)
        
        # URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        url_label.setMinimumWidth(60)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        self.url_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                color: black;
                border: 2px solid #e1e8ed;
                border-radius: 6px;
                padding: 6px;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background-color: white;
                color: black;
            }
        """)
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_link_data(self) -> tuple[str, str]:
        """
        Get the link text and URL.
        
        Returns:
            Tuple of (text, url)
        """
        return self.text_input.text().strip(), self.url_input.text().strip()


class EmojiDialog(QDialog):
    """Dialog for selecting emojis."""
    
    # Common emojis organized by category
    EMOJIS = [
        # Smileys
        "😀", "😃", "😄", "😁", "😆", "😅", "🤣", "😂",
        "🙂", "🙃", "😉", "😊", "😇", "🥰", "😍", "🤩",
        "😘", "😗", "😚", "😙", "😋", "😛", "😜", "🤪",
        # Gestures
        "👍", "👎", "👌", "✌️", "🤞", "🤟", "🤘", "🤙",
        "👏", "🙌", "👐", "🤲", "🤝", "🙏", "✍️", "💪",
        # Hearts
        "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍",
        "💔", "❣️", "💕", "💞", "💓", "💗", "💖", "💘",
        # Objects
        "🎉", "🎊", "🎈", "🎁", "🏆", "🥇", "🥈", "🥉",
        "⭐", "🌟", "✨", "💫", "🔥", "💯", "✅", "❌",
    ]
    
    def __init__(self, parent=None):
        """Initialize the emoji dialog."""
        super().__init__(parent)
        self.setWindowTitle("Выбрать эмодзи")
        self.setModal(True)
        
        self.selected_emoji: Optional[str] = None
        
        layout = QVBoxLayout()
        
        # Create grid of emoji buttons
        grid = QGridLayout()
        grid.setSpacing(5)
        
        row = 0
        col = 0
        for emoji in self.EMOJIS:
            btn = QPushButton(emoji)
            btn.setFixedSize(40, 40)
            btn.setStyleSheet("font-size: 20px;")
            btn.clicked.connect(lambda checked, e=emoji: self.select_emoji(e))
            grid.addWidget(btn, row, col)
            
            col += 1
            if col >= 8:  # 8 emojis per row
                col = 0
                row += 1
        
        layout.addLayout(grid)
        
        # Cancel button
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        self.setLayout(layout)
    
    def select_emoji(self, emoji: str) -> None:
        """
        Select an emoji and close the dialog.
        
        Args:
            emoji: The selected emoji
        """
        self.selected_emoji = emoji
        self.accept()
    
    def get_emoji(self) -> Optional[str]:
        """
        Get the selected emoji.
        
        Returns:
            The selected emoji or None
        """
        return self.selected_emoji


class TextEditorPanel(QWidget):
    """
    Text editor panel with rich text formatting.
    
    Provides:
    - Rich text editing with QTextEdit
    - Dynamic height adjustment based on content
    - Formatting toolbar (Bold, Italic, Underline, Color, Link, Emoji)
    - HTML conversion for Telegram API
    - Manual save functionality
    
    Signals:
        message_saved: Emitted when message is manually saved (html_content, plain_text)
    """
    
    message_saved = pyqtSignal(str, str, bool)  # html_content, plain_text, disable_preview
    
    def __init__(self, parent=None):
        """Initialize the text editor panel."""
        super().__init__(parent)
        
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Create text_edit first (для toolbar)
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Введите ваше сообщение здесь...")
        # Фиксированная высота с scrollbar
        self.text_edit.setMinimumHeight(200)
        self.text_edit.setMaximumHeight(400)
        # ВСЕГДА показывать scrollbar
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # Включить прокрутку колесиком мыши
        self.text_edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # ВСЕГДА белый фон и черный текст
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: white;
                color: black;
                border: 2px solid #e1e8ed;
                border-radius: 6px;
                padding: 8px;
            }
            QTextEdit:focus {
                border-color: #3498db;
                background-color: white;
                color: black;
            }
        """)
        
        # 2. TOOLBAR (сверху)
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar, stretch=0)
        
        # 3. TEXT EDITOR (фиксированная высота со scrollbar)
        layout.addWidget(self.text_edit, stretch=0)
        
        # 4. Checkbox для отключения превью ссылок
        self.disable_preview_checkbox = QCheckBox("Убрать превью ссылки")
        self.disable_preview_checkbox.setToolTip("При включении ссылки будут отправляться без превью")
        self.disable_preview_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                color: #2c3e50;
                padding: 8px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #3498db;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #3498db;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #2980b9;
            }
            QCheckBox:hover {
                color: #3498db;
            }
        """)
        layout.addWidget(self.disable_preview_checkbox, stretch=0)
        
        # 5. SAVE BUTTON (внизу)
        self.save_btn = QPushButton("Сохранить сообщение")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setMaximumHeight(40)
        self.save_btn.clicked.connect(self.save_message)
        layout.addWidget(self.save_btn, stretch=0)
        
        # Добавляем stretch в конце чтобы все элементы были сверху
        layout.addStretch(1)
    
    # Метод adjust_editor_height больше не используется
    # QTextEdit имеет фиксированную высоту и scrollbar
    
    def create_toolbar(self) -> QToolBar:
        """
        Create formatting toolbar.
        
        Returns:
            QToolBar with formatting actions
        """
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        
        # Bold action
        bold_action = QAction("Жирный", self)
        bold_action.setShortcut("Ctrl+B")
        bold_action.setCheckable(True)
        bold_action.triggered.connect(self.apply_bold)
        toolbar.addAction(bold_action)
        self.bold_action = bold_action
        
        # Italic action
        italic_action = QAction("Курсив", self)
        italic_action.setShortcut("Ctrl+I")
        italic_action.setCheckable(True)
        italic_action.triggered.connect(self.apply_italic)
        toolbar.addAction(italic_action)
        self.italic_action = italic_action
        
        # Underline action
        underline_action = QAction("Подчеркнутый", self)
        underline_action.setShortcut("Ctrl+U")
        underline_action.setCheckable(True)
        underline_action.triggered.connect(self.apply_underline)
        toolbar.addAction(underline_action)
        self.underline_action = underline_action
        
        toolbar.addSeparator()
        
        # Color action
        color_action = QAction("Цвет текста", self)
        color_action.triggered.connect(self.change_text_color)
        toolbar.addAction(color_action)
        
        toolbar.addSeparator()
        
        # Link action
        link_action = QAction("Ссылка", self)
        link_action.setShortcut("Ctrl+K")
        link_action.triggered.connect(self.insert_link)
        toolbar.addAction(link_action)
        
        # Emoji action
        emoji_action = QAction("Эмодзи", self)
        emoji_action.triggered.connect(self.insert_emoji)
        toolbar.addAction(emoji_action)
        
        # Connect cursor position changed to update toolbar state
        self.text_edit.cursorPositionChanged.connect(self.update_toolbar_state)
        
        return toolbar
    
    def update_toolbar_state(self) -> None:
        """Update toolbar button states based on current format."""
        cursor = self.text_edit.textCursor()
        char_format = cursor.charFormat()
        
        # Update bold state
        self.bold_action.setChecked(char_format.fontWeight() == QFont.Weight.Bold)
        
        # Update italic state
        self.italic_action.setChecked(char_format.fontItalic())
        
        # Update underline state
        self.underline_action.setChecked(char_format.fontUnderline())
    
    def apply_bold(self) -> None:
        """Apply bold formatting to selected text."""
        cursor = self.text_edit.textCursor()
        
        if cursor.hasSelection():
            char_format = QTextCharFormat()
            
            # Toggle bold
            current_format = cursor.charFormat()
            if current_format.fontWeight() == QFont.Weight.Bold:
                char_format.setFontWeight(QFont.Weight.Normal)
            else:
                char_format.setFontWeight(QFont.Weight.Bold)
            
            cursor.mergeCharFormat(char_format)
            self.text_edit.setTextCursor(cursor)
    
    def apply_italic(self) -> None:
        """Apply italic formatting to selected text."""
        cursor = self.text_edit.textCursor()
        
        if cursor.hasSelection():
            char_format = QTextCharFormat()
            
            # Toggle italic
            current_format = cursor.charFormat()
            char_format.setFontItalic(not current_format.fontItalic())
            
            cursor.mergeCharFormat(char_format)
            self.text_edit.setTextCursor(cursor)
    
    def apply_underline(self) -> None:
        """Apply underline formatting to selected text."""
        cursor = self.text_edit.textCursor()
        
        if cursor.hasSelection():
            char_format = QTextCharFormat()
            
            # Toggle underline
            current_format = cursor.charFormat()
            char_format.setFontUnderline(not current_format.fontUnderline())
            
            cursor.mergeCharFormat(char_format)
            self.text_edit.setTextCursor(cursor)
    
    def change_text_color(self) -> None:
        """Open color picker and apply color to selected text."""
        # Get current color
        cursor = self.text_edit.textCursor()
        current_color = cursor.charFormat().foreground().color()
        
        # Open color dialog
        color = QColorDialog.getColor(current_color, self, "Выберите цвет текста")
        
        if color.isValid():
            # Apply color to selection or set for next input
            char_format = QTextCharFormat()
            char_format.setForeground(color)
            
            if cursor.hasSelection():
                cursor.mergeCharFormat(char_format)
                self.text_edit.setTextCursor(cursor)
            else:
                # Set format for next input
                self.text_edit.setCurrentCharFormat(char_format)
    
    def insert_link(self) -> None:
        """Insert a link at cursor position or around selected text."""
        cursor = self.text_edit.textCursor()
        
        # Get selected text if any
        selected_text = cursor.selectedText()
        
        # Show link dialog
        dialog = LinkDialog(self)
        if selected_text:
            dialog.text_input.setText(selected_text)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            text, url = dialog.get_link_data()
            
            if not text or not url:
                QMessageBox.warning(self, "Неверная ссылка", "Требуются и текст, и URL.")
                return
            
            # Insert link
            char_format = QTextCharFormat()
            char_format.setAnchor(True)
            char_format.setAnchorHref(url)
            char_format.setFontUnderline(True)
            
            if cursor.hasSelection():
                # Replace selection with link
                cursor.removeSelectedText()
            
            cursor.insertText(text, char_format)
            self.text_edit.setTextCursor(cursor)
    
    def insert_emoji(self) -> None:
        """Open emoji picker and insert selected emoji."""
        dialog = EmojiDialog(self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            emoji = dialog.get_emoji()
            if emoji:
                cursor = self.text_edit.textCursor()
                cursor.insertText(emoji)
                self.text_edit.setTextCursor(cursor)
    
    def get_html_content(self) -> str:
        """
        Get content as HTML formatted for Telegram API.
        
        Converts Qt HTML to Telegram-compatible HTML tags:
        - <b> for bold
        - <i> for italic
        - <u> for underline
        - <a href="..."> for links
        
        Returns:
            HTML string compatible with Telegram API
        """
        # Get HTML from QTextEdit
        html = self.text_edit.toHtml()
        
        # Parse and convert to Telegram HTML
        telegram_html = self._convert_to_telegram_html(html)
        
        return telegram_html
    
    def _convert_to_telegram_html(self, qt_html: str) -> str:
        """
        Convert Qt HTML to Telegram HTML.
        
        Args:
            qt_html: HTML from QTextEdit
            
        Returns:
            Telegram-compatible HTML
        """
        import re
        from html.parser import HTMLParser
        
        # Remove CSS styles block that Qt adds
        # Remove everything before <body> or first <p>
        qt_html = re.sub(r'<!DOCTYPE[^>]*>', '', qt_html)
        qt_html = re.sub(r'<html[^>]*>', '', qt_html)
        qt_html = re.sub(r'</html>', '', qt_html)
        qt_html = re.sub(r'<head>.*?</head>', '', qt_html, flags=re.DOTALL)
        qt_html = re.sub(r'<style[^>]*>.*?</style>', '', qt_html, flags=re.DOTALL)
        qt_html = re.sub(r'<body[^>]*>', '', qt_html)
        qt_html = re.sub(r'</body>', '', qt_html)
        
        class TelegramHTMLConverter(HTMLParser):
            """Convert Qt HTML to Telegram HTML."""
            
            def __init__(self):
                super().__init__()
                self.result = []
                self.bold = False
                self.italic = False
                self.underline = False
                self.link_href = None
            
            def handle_starttag(self, tag, attrs):
                attrs_dict = dict(attrs)
                
                if tag == 'span':
                    # Check for font-weight (bold)
                    style = attrs_dict.get('style', '')
                    if 'font-weight:600' in style or 'font-weight: 600' in style or 'font-weight:bold' in style:
                        self.bold = True
                        self.result.append('<b>')
                    
                    # Check for font-style (italic)
                    if 'font-style:italic' in style or 'font-style: italic' in style:
                        self.italic = True
                        self.result.append('<i>')
                    
                    # Check for text-decoration (underline)
                    if 'text-decoration: underline' in style or 'text-decoration:underline' in style:
                        self.underline = True
                        self.result.append('<u>')
                
                elif tag == 'a':
                    href = attrs_dict.get('href', '')
                    if href:
                        self.link_href = href
                        self.result.append(f'<a href="{href}">')
                
                elif tag == 'strong' or tag == 'b':
                    self.bold = True
                    self.result.append('<b>')
                
                elif tag == 'em' or tag == 'i':
                    self.italic = True
                    self.result.append('<i>')
                
                elif tag == 'u':
                    self.underline = True
                    self.result.append('<u>')
            
            def handle_endtag(self, tag):
                if tag == 'span':
                    if self.underline:
                        self.result.append('</u>')
                        self.underline = False
                    if self.italic:
                        self.result.append('</i>')
                        self.italic = False
                    if self.bold:
                        self.result.append('</b>')
                        self.bold = False
                
                elif tag == 'a':
                    if self.link_href:
                        self.result.append('</a>')
                        self.link_href = None
                
                elif tag == 'strong' or tag == 'b':
                    if self.bold:
                        self.result.append('</b>')
                        self.bold = False
                
                elif tag == 'em' or tag == 'i':
                    if self.italic:
                        self.result.append('</i>')
                        self.italic = False
                
                elif tag == 'u':
                    if self.underline:
                        self.result.append('</u>')
                        self.underline = False
                
                elif tag == 'p' or tag == 'br':
                    self.result.append('\n')
            
            def handle_data(self, data):
                # Don't strip - preserve spaces
                if data:
                    self.result.append(data)
            
            def get_result(self):
                result = ''.join(self.result)
                # Clean up multiple newlines but preserve single ones
                result = re.sub(r'\n{3,}', '\n\n', result)
                return result.strip()
        
        converter = TelegramHTMLConverter()
        converter.feed(qt_html)
        return converter.get_result()
    
    def get_plain_text(self) -> str:
        """
        Get plain text content without formatting.
        
        Returns:
            Plain text string
        """
        return self.text_edit.toPlainText()
    
    def save_message(self) -> None:
        """Save message and emit signal."""
        html_content = self.get_html_content()
        plain_text = self.get_plain_text()
        disable_preview = self.disable_preview_checkbox.isChecked()
        
        if not plain_text.strip():
            QMessageBox.warning(self, "Пустое сообщение", "Пожалуйста, введите сообщение перед сохранением.")
            return
        
        self.message_saved.emit(html_content, plain_text, disable_preview)
        
        preview_status = "без превью" if disable_preview else "с превью"
        QMessageBox.information(
            self,
            "Сообщение сохранено",
            f"Сообщение успешно сохранено ({preview_status})!"
        )
    
    def set_content(self, html: str) -> None:
        """
        Set editor content from HTML.
        
        Args:
            html: HTML content to set
        """
        self.text_edit.setHtml(html)
    
    def clear(self) -> None:
        """Clear editor content."""
        self.text_edit.clear()
