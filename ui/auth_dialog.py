"""
Authentication Dialog for Telegram Mailer MacOS App.

Provides a GUI dialog for Telegram authentication with:
- Phone number input
- SMS code verification
- 2FA password input (if enabled)
- Error handling and user feedback
"""

from typing import Optional, Tuple

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal
from telethon.errors import (
    PhoneNumberInvalidError,
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
    PasswordHashInvalidError,
)

from telegram.telegram_service import TelegramService


class AuthDialog(QDialog):
    """
    Dialog for Telegram authentication.
    
    Handles the complete authentication flow:
    1. Phone number input
    2. Code request
    3. Code verification
    4. 2FA password (if needed)
    
    Signals:
        authentication_success: Emitted when authentication is successful
    """
    
    authentication_success = pyqtSignal()
    
    def __init__(self, telegram_service: TelegramService, parent: Optional[QWidget] = None):
        """
        Initialize authentication dialog.
        
        Args:
            telegram_service: TelegramService instance for authentication
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.telegram_service = telegram_service
        self.phone_code_hash: Optional[str] = None
        self.current_phone: Optional[str] = None
        self.needs_2fa = False
        
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup UI components."""
        self.setWindowTitle("Авторизация Telegram")
        self.setMinimumWidth(400)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Вход в Telegram")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Phone number section
        self.phone_label = QLabel("Номер телефона:")
        layout.addWidget(self.phone_label)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+7XXXXXXXXXX")
        self.phone_input.setMinimumHeight(35)
        self.phone_input.setStyleSheet("""
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
        layout.addWidget(self.phone_input)
        
        self.send_code_btn = QPushButton("Отправить код")
        self.send_code_btn.setMinimumHeight(40)
        self.send_code_btn.clicked.connect(self.send_code)
        layout.addWidget(self.send_code_btn)
        
        # Code section (initially hidden)
        self.code_label = QLabel("Код из SMS:")
        self.code_label.hide()
        layout.addWidget(self.code_label)
        
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("12345")
        self.code_input.setMinimumHeight(35)
        self.code_input.setStyleSheet("""
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
        self.code_input.hide()
        layout.addWidget(self.code_input)
        
        self.verify_code_btn = QPushButton("Подтвердить код")
        self.verify_code_btn.setMinimumHeight(40)
        self.verify_code_btn.clicked.connect(self.verify_code)
        self.verify_code_btn.hide()
        layout.addWidget(self.verify_code_btn)
        
        # 2FA password section (initially hidden)
        self.password_label = QLabel("Пароль двухфакторной аутентификации:")
        self.password_label.hide()
        layout.addWidget(self.password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Введите пароль 2FA")
        self.password_input.setMinimumHeight(35)
        self.password_input.setStyleSheet("""
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
        self.password_input.hide()
        layout.addWidget(self.password_input)
        
        self.verify_password_btn = QPushButton("Подтвердить пароль")
        self.verify_password_btn.setMinimumHeight(40)
        self.verify_password_btn.clicked.connect(self.verify_password)
        self.verify_password_btn.hide()
        layout.addWidget(self.verify_password_btn)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Cancel button
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn)
    
    def send_code(self) -> None:
        """Send authentication code to phone number."""
        phone = self.phone_input.text().strip()
        
        if not phone:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите номер телефона")
            return
        
        if not phone.startswith("+"):
            QMessageBox.warning(
                self,
                "Ошибка",
                "Номер телефона должен начинаться с '+' и кода страны\n"
                "Например: +79123456789"
            )
            return
        
        self.status_label.setText("Отправка кода...")
        self.send_code_btn.setEnabled(False)
        
        import asyncio
        
        async def send_code_async():
            try:
                # Connect if not connected
                if not self.telegram_service.is_connected:
                    await self.telegram_service.connect()
                
                # Send code request
                phone_code_hash = await self.telegram_service.send_code_request(phone)
                return phone_code_hash, None
            except PhoneNumberInvalidError:
                return None, "Неверный номер телефона. Проверьте формат."
            except Exception as e:
                return None, f"Ошибка: {str(e)}"
        
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        phone_code_hash, error = loop.run_until_complete(send_code_async())
        
        if error:
            QMessageBox.critical(self, "Ошибка", error)
            self.status_label.setText("")
            self.send_code_btn.setEnabled(True)
        else:
            self.phone_code_hash = phone_code_hash
            self.current_phone = phone
            
            # Show code input section
            self.phone_input.setEnabled(False)
            self.send_code_btn.hide()
            
            self.code_label.show()
            self.code_input.show()
            self.verify_code_btn.show()
            
            self.status_label.setText("Код отправлен! Проверьте SMS или Telegram.")
            self.status_label.setStyleSheet("color: green;")
    
    def verify_code(self) -> None:
        """Verify authentication code."""
        code = self.code_input.text().strip()
        
        if not code:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите код")
            return
        
        if not self.phone_code_hash or not self.current_phone:
            QMessageBox.critical(self, "Ошибка", "Сначала запросите код")
            return
        
        self.status_label.setText("Проверка кода...")
        self.status_label.setStyleSheet("")
        self.verify_code_btn.setEnabled(False)
        
        import asyncio
        
        async def verify_code_async():
            try:
                success = await self.telegram_service.sign_in(
                    phone=self.current_phone,
                    code=code,
                    phone_code_hash=self.phone_code_hash
                )
                return success, None, False
            except PhoneCodeInvalidError:
                return False, "Неверный код. Попробуйте еще раз.", False
            except SessionPasswordNeededError:
                return False, None, True  # Need 2FA password
            except Exception as e:
                return False, f"Ошибка: {str(e)}", False
        
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        success, error, needs_2fa = loop.run_until_complete(verify_code_async())
        
        if needs_2fa:
            # Show 2FA password input
            self.code_input.setEnabled(False)
            self.verify_code_btn.hide()
            
            self.password_label.show()
            self.password_input.show()
            self.verify_password_btn.show()
            
            self.status_label.setText("Требуется пароль двухфакторной аутентификации")
            self.status_label.setStyleSheet("color: orange;")
            self.needs_2fa = True
        elif error:
            QMessageBox.critical(self, "Ошибка", error)
            self.status_label.setText("")
            self.verify_code_btn.setEnabled(True)
        elif success:
            self.status_label.setText("Успешная авторизация!")
            self.status_label.setStyleSheet("color: green;")
            self.authentication_success.emit()
            self.accept()
    
    def verify_password(self) -> None:
        """Verify 2FA password."""
        password = self.password_input.text()
        
        if not password:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите пароль")
            return
        
        if not self.current_phone or not self.phone_code_hash:
            QMessageBox.critical(self, "Ошибка", "Ошибка процесса авторизации")
            return
        
        self.status_label.setText("Проверка пароля...")
        self.status_label.setStyleSheet("")
        self.verify_password_btn.setEnabled(False)
        
        import asyncio
        
        async def verify_password_async():
            try:
                # Get the code that was entered
                code = self.code_input.text().strip()
                
                success = await self.telegram_service.sign_in(
                    phone=self.current_phone,
                    code=code,
                    phone_code_hash=self.phone_code_hash,
                    password=password
                )
                return success, None
            except PasswordHashInvalidError:
                return False, "Неверный пароль. Попробуйте еще раз."
            except Exception as e:
                return False, f"Ошибка: {str(e)}"
        
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        success, error = loop.run_until_complete(verify_password_async())
        
        if error:
            QMessageBox.critical(self, "Ошибка", error)
            self.status_label.setText("")
            self.verify_password_btn.setEnabled(True)
        elif success:
            self.status_label.setText("Успешная авторизация!")
            self.status_label.setStyleSheet("color: green;")
            self.authentication_success.emit()
            self.accept()
