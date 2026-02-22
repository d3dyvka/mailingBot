"""
Main Window for Telegram Mailer MacOS App.

Provides the main application window with:
- Configuration panel for API credentials
- Authentication panel for Telegram login
- Group selection and member count display
- End date input for mailing campaign
- Window geometry persistence
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QDateTimeEdit,
    QGroupBox,
    QApplication,
    QDialog,
)
from PyQt6.QtCore import Qt, QSettings, QDateTime, pyqtSignal
from PyQt6.QtGui import QCloseEvent

from config.config_manager import ConfigManager
from telegram.telegram_service import TelegramService
from utils.delay_calculator import DelayCalculator
from utils.constants import CONFIG_DIR, SESSION_DIR
from ui.text_editor_panel import TextEditorPanel
from ui.progress_panel import ProgressPanel
from ui.auth_dialog import AuthDialog


class MainWindow(QMainWindow):
    """
    Main application window.
    
    Coordinates all panels and manages application lifecycle.
    Provides native MacOS design and window geometry persistence.
    
    Signals:
        credentials_saved: Emitted when API credentials are saved
        authenticated: Emitted when user successfully authenticates
        group_selected: Emitted when a group is selected and members loaded
    """
    
    credentials_saved = pyqtSignal(str, str)  # api_id, api_hash
    authenticated = pyqtSignal()
    group_selected = pyqtSignal(int)  # member_count
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Hardcoded credentials
        self.API_ID = "22937843"
        self.API_HASH = "f059dadbb0d4d4734feb75dd4fdcb4b9"
        
        # Initialize managers
        self.config_manager = ConfigManager(CONFIG_DIR)
        self.telegram_service = TelegramService(self.API_ID, self.API_HASH, SESSION_DIR)
        self.delay_calculator = DelayCalculator()
        
        # Initialize mailing components
        from utils.progress_tracker import ProgressTracker
        from utils.error_logger import ErrorLogger
        from utils.power_manager import PowerManager
        from telegram.mailing_service import MailingService
        from utils.constants import PROGRESS_DIR, LOG_DIR
        
        self.progress_tracker = ProgressTracker(PROGRESS_DIR)
        self.error_logger = ErrorLogger(LOG_DIR)
        self.power_manager = PowerManager()
        self.mailing_service = MailingService(
            telegram_service=self.telegram_service,
            progress_tracker=self.progress_tracker,
            delay_calculator=self.delay_calculator,
            error_logger=self.error_logger,
            power_manager=self.power_manager
        )
        
        # Store loaded members
        self.loaded_members: List = []
        self.current_group_url: str = ""
        
        # Settings for window geometry persistence
        self.settings = QSettings("TelegramMailer", "MainWindow")
        
        # Authentication state
        self.phone_code_hash: Optional[str] = None
        self.current_phone: Optional[str] = None
        self.member_count: int = 0
        
        # Message content
        self.message_html: Optional[str] = None
        self.message_plain: Optional[str] = None
        self.disable_link_preview: bool = False
        
        # Setup UI
        self.setup_ui()
        
        # Load window geometry
        self.load_window_geometry()
        
        # Check if already authenticated
        self.check_existing_session()
    
    def setup_ui(self) -> None:
        """Setup UI components and layout."""
        self.setWindowTitle("Telegram Рассыльщик")
        self.setMinimumSize(800, 900)
        
        # Set modern color scheme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f7fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e1e8ed;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #2c3e50;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            QLineEdit, QDateTimeEdit {
                border: 2px solid #e1e8ed;
                border-radius: 6px;
                padding: 6px;
                background-color: white;
                color: black;
            }
            QLineEdit:focus, QDateTimeEdit:focus {
                border-color: #3498db;
                background-color: white;
                color: black;
            }
            QLineEdit:disabled, QDateTimeEdit:disabled {
                background-color: #f5f5f5;
                color: #7f8c8d;
            }
            QTextEdit, QPlainTextEdit {
                border: 2px solid #e1e8ed;
                border-radius: 6px;
                padding: 6px;
                background-color: white;
                color: black;
            }
            QTextEdit:focus, QPlainTextEdit:focus {
                border-color: #3498db;
                background-color: white;
                color: black;
            }
            QLabel {
                color: #2c3e50;
            }
            QStatusBar {
                background-color: #ecf0f1;
                color: #2c3e50;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add panels
        main_layout.addWidget(self.create_group_panel())
        main_layout.addWidget(self.create_end_date_panel())
        
        # Add Text Editor Panel
        editor_group = QGroupBox("Редактор сообщений")
        editor_layout = QVBoxLayout()
        editor_layout.setSpacing(0)
        editor_layout.setContentsMargins(5, 5, 5, 5)
        self.text_editor_panel = TextEditorPanel()
        self.text_editor_panel.message_saved.connect(self.on_message_saved)
        editor_layout.addWidget(self.text_editor_panel)
        editor_group.setLayout(editor_layout)
        main_layout.addWidget(editor_group)
        
        # Add Progress Panel
        self.progress_panel = ProgressPanel()
        self.progress_panel.reset_progress_clicked.connect(self.on_reset_progress)
        self.progress_panel.logout_clicked.connect(self.logout)
        self.progress_panel.start_mailing_clicked.connect(self.on_start_mailing)
        main_layout.addWidget(self.progress_panel)
        
        # Add stretch to push everything to the top
        main_layout.addStretch()
        
        # Status bar
        self.statusBar().showMessage("Готов")
    

    
    def create_group_panel(self) -> QGroupBox:
        """
        Create group selection panel.
        
        Returns:
            QGroupBox containing group URL input and member count display
        """
        group = QGroupBox("Выбор группы")
        layout = QVBoxLayout()
        
        # Group URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("Ссылка на группу:")
        url_label.setMinimumWidth(150)
        self.group_url_input = QLineEdit()
        self.group_url_input.setMinimumHeight(35)
        self.group_url_input.setPlaceholderText("Введите ссылку на группу или username")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.group_url_input)
        layout.addLayout(url_layout)
        
        # Load members button
        self.load_members_btn = QPushButton("Загрузить участников")
        self.load_members_btn.clicked.connect(self.load_group_members)
        self.load_members_btn.setMinimumHeight(40)
        layout.addWidget(self.load_members_btn)
        
        # Logout button
        self.logout_btn = QPushButton("Выйти")
        self.logout_btn.clicked.connect(self.logout)
        self.logout_btn.hide()
        self.logout_btn.setMinimumHeight(40)
        layout.addWidget(self.logout_btn)
        
        # Member count display
        self.member_count_label = QLabel("Участников: Не загружено")
        self.member_count_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.member_count_label)
        
        group.setLayout(layout)
        return group
    
    def create_end_date_panel(self) -> QGroupBox:
        """
        Create end date selection panel.
        
        Returns:
            QGroupBox containing end date input and delay calculation display
        """
        group = QGroupBox("Дата окончания рассылки")
        layout = QVBoxLayout()
        
        # End date input
        date_layout = QHBoxLayout()
        date_label = QLabel("Дата окончания:")
        date_label.setMinimumWidth(150)
        self.end_date_input = QDateTimeEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.end_date_input.setDateTime(QDateTime.currentDateTime().addDays(30))
        self.end_date_input.setMinimumHeight(35)
        self.end_date_input.dateTimeChanged.connect(self.calculate_delay)
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.end_date_input)
        layout.addLayout(date_layout)
        
        # Calculate button
        self.calculate_btn = QPushButton("Рассчитать задержку")
        self.calculate_btn.clicked.connect(self.calculate_delay)
        self.calculate_btn.setMinimumHeight(40)
        layout.addWidget(self.calculate_btn)
        
        # Delay info display
        self.delay_info_label = QLabel("Задержка: Не рассчитана")
        self.delay_info_label.setWordWrap(True)
        self.delay_info_label.setMinimumHeight(80)
        self.delay_info_label.setStyleSheet("padding: 10px; background-color: #f5f5f5; border-radius: 5px;")
        self.delay_info_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.delay_info_label)
        
        group.setLayout(layout)
        return group
    

    def check_existing_session(self) -> None:
        """Check if there's an existing valid session."""
        if not self.telegram_service:
            return
        
        import asyncio
        
        async def check_auth():
            try:
                await self.telegram_service.connect()
                if await self.telegram_service.is_authorized():
                    return True
            except Exception:
                pass
            return False
        
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        is_auth = loop.run_until_complete(check_auth())
        
        if is_auth:
            self.on_authentication_success()
        else:
            # Show authentication dialog
            self.show_auth_dialog()
    
    def show_auth_dialog(self) -> None:
        """Show authentication dialog."""
        auth_dialog = AuthDialog(self.telegram_service, self)
        auth_dialog.authentication_success.connect(self.on_authentication_success)
        
        result = auth_dialog.exec()
        
        if result == QDialog.DialogCode.Rejected:
            # User cancelled authentication
            self.statusBar().showMessage("Авторизация отменена")
    
    def on_authentication_success(self) -> None:
        """Handle successful authentication."""
        self.statusBar().showMessage("Успешная аутентификация!")
        
        # Show logout button
        self.logout_btn.show()
        
        # Enable group input
        self.group_url_input.setEnabled(True)
        
        self.authenticated.emit()
    
    def logout(self) -> None:
        """Logout and clear session."""
        reply = QMessageBox.question(
            self,
            "Подтверждение выхода",
            "Вы уверены, что хотите выйти? Это удалит файл сессии.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Delete session file
            session_file = SESSION_DIR / "session_name.session"
            if session_file.exists():
                session_file.unlink()
            
            # Reset UI
            self.group_url_input.clear()
            self.group_url_input.setEnabled(False)
            self.member_count_label.setText("Участников: Не загружено")
            
            # Hide logout button
            self.logout_btn.hide()
            
            # Disable panels
            self.end_date_input.setEnabled(False)
            self.calculate_btn.setEnabled(False)
            
            self.statusBar().showMessage("Вы вышли из системы")
            
            QMessageBox.information(self, "Выход выполнен", "Вы успешно вышли из системы. Пожалуйста, перезапустите приложение для повторного входа.")
    
    def load_group_members(self) -> None:
        """Load group members."""
        if not self.telegram_service:
            QMessageBox.warning(self, "Ошибка", "Сервис Telegram не инициализирован")
            return
        
        # Check if authorized first
        import asyncio
        
        async def check_and_auth():
            try:
                # Check if authorized
                if not await self.telegram_service.is_authorized():
                    return False, "Не авторизован"
                
                return True, None
            except Exception as e:
                return False, str(e)
        
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        is_auth, error = loop.run_until_complete(check_and_auth())
        
        if not is_auth:
            # Show authentication dialog
            self.show_auth_dialog()
            return
        
        group_url = self.group_url_input.text().strip()
        if not group_url:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите ссылку на группу")
            return
        
        self.statusBar().showMessage("Загрузка участников группы...")
        
        async def load_members_async():
            try:
                members = await self.telegram_service.get_group_members(group_url)
                return members, None
            except Exception as e:
                return None, str(e)
        
        members, error = loop.run_until_complete(load_members_async())
        
        if error:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить участников: {error}")
            self.statusBar().showMessage("Не удалось загрузить участников")
        else:
            self.member_count = len(members)
            self.loaded_members = members  # Store loaded members
            self.current_group_url = group_url  # Store group URL
            self.member_count_label.setText(f"Участников: {self.member_count}")
            self.statusBar().showMessage(f"Загружено {self.member_count} участников")
            
            # Enable end date panel
            self.end_date_input.setEnabled(True)
            self.calculate_btn.setEnabled(True)
            
            # Set total users in progress panel
            self.progress_panel.set_total_users(self.member_count)
            
            self.group_selected.emit(self.member_count)
            
            QMessageBox.information(
                self,
                "Успех",
                f"Загружено {self.member_count} участников из группы!"
            )
    
    def calculate_delay(self) -> None:
        """Calculate optimal delay between batches."""
        if self.member_count == 0:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, сначала загрузите участников группы")
            return
        
        end_date = self.end_date_input.dateTime().toPyDateTime()
        
        try:
            result = self.delay_calculator.calculate_delay(
                total_users=self.member_count,
                end_date=end_date
            )
            
            # Display result
            info_text = f"Задержка: {result.delay_hours:.2f} часов\n"
            info_text += f"Батчей: {result.num_batches}\n"
            info_text += f"Ожидаемое завершение: {result.estimated_completion.strftime('%d.%m.%Y %H:%M')}\n"
            
            if result.warning:
                info_text += f"\n⚠️ {result.warning}"
                self.delay_info_label.setStyleSheet("color: orange; font-weight: bold;")
            elif result.is_safe:
                info_text += "\n✓ Задержка безопасна"
                self.delay_info_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.delay_info_label.setStyleSheet("color: red; font-weight: bold;")
            
            self.delay_info_label.setText(info_text)
            self.statusBar().showMessage("Задержка рассчитана")
            
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
    
    def on_message_saved(self, html_content: str, plain_text: str, disable_preview: bool) -> None:
        """
        Handle message saved from text editor.
        
        Args:
            html_content: HTML formatted message
            plain_text: Plain text message
            disable_preview: Whether to disable link preview
        """
        self.message_html = html_content
        self.message_plain = plain_text
        self.disable_link_preview = disable_preview
        preview_status = "без превью" if disable_preview else "с превью"
        self.statusBar().showMessage(f"Сообщение сохранено ({preview_status})")
    
    def on_reset_progress(self) -> None:
        """Handle reset progress request."""
        # Reset progress panel
        self.progress_panel.reset_progress()
        
        # Reset progress tracker file
        if self.current_group_url:
            self.progress_tracker.reset_progress(self.current_group_url)
        
        self.statusBar().showMessage("Прогресс сброшен")
        
        QMessageBox.information(
            self,
            "Прогресс сброшен",
            "Прогресс успешно сброшен."
        )
    
    def on_start_mailing(self) -> None:
        """Handle start mailing request."""
        # Validate that all required data is present
        if self.member_count == 0:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Пожалуйста, сначала загрузите участников группы."
            )
            return
        
        if not self.message_html or not self.message_plain:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Пожалуйста, сначала создайте и сохраните сообщение."
            )
            return
        
        # Check if delay is calculated
        if "Не рассчитана" in self.delay_info_label.text():
            QMessageBox.warning(
                self,
                "Ошибка",
                "Пожалуйста, сначала рассчитайте задержку."
            )
            return
        
        # Confirm start
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Начать рассылку для {self.member_count} участников?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Check if previous mailing was completed
            # If all users were sent, reset progress automatically
            if self.current_group_url:
                try:
                    self.progress_tracker.load_progress(self.current_group_url)
                    stats = self.progress_tracker.get_statistics()
                    
                    if stats['sent_count'] > 0 and stats['remaining_count'] == 0:
                        # Previous mailing was completed, reset automatically
                        reply_reset = QMessageBox.question(
                            self,
                            "Предыдущая рассылка завершена",
                            "Предыдущая рассылка для этой группы была завершена.\n"
                            "Начать новую рассылку? (Прогресс будет сброшен)",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                        )
                        
                        if reply_reset == QMessageBox.StandardButton.Yes:
                            # Reset progress for new mailing
                            self.progress_tracker.reset_progress(self.current_group_url)
                            self.progress_panel.reset_progress()
                            self.statusBar().showMessage("Прогресс сброшен для новой рассылки")
                        else:
                            return
                except Exception as e:
                    # If there's an error loading progress, just continue
                    print(f"Error checking progress: {e}")
            
            # Start mailing in background
            self.statusBar().showMessage("Рассылка начата...")
            
            # Disable start button during mailing
            self.progress_panel.start_mailing_btn.setEnabled(False)
            
            # Start mailing asynchronously using QTimer
            from PyQt6.QtCore import QTimer
            
            def start_async_mailing():
                import asyncio
                
                async def run_mailing():
                    try:
                        end_date = self.end_date_input.dateTime().toPyDateTime()
                        
                        # Progress callback
                        def on_progress(user, result):
                            try:
                                if result.success:
                                    self.progress_panel.increment_sent()
                                else:
                                    self.progress_panel.increment_failed()
                            except Exception as e:
                                print(f"Error in progress callback: {e}")
                        
                        # Batch callback
                        def on_batch_complete(delay_seconds):
                            try:
                                self.progress_panel.start_countdown(
                                    int(delay_seconds),
                                    "Ожидание между батчами"
                                )
                            except Exception as e:
                                print(f"Error in batch callback: {e}")
                        
                        # Start mailing
                        stats = await self.mailing_service.start_mailing(
                            users=self.loaded_members,
                            message=self.message_html,
                            group_url=self.current_group_url,
                            end_date=end_date,
                            progress_callback=on_progress,
                            batch_callback=on_batch_complete,
                            link_preview=not self.disable_link_preview
                        )
                        
                        # Show completion message
                        QMessageBox.information(
                            self,
                            "Рассылка завершена",
                            f"Рассылка завершена!\n\n"
                            f"Отправлено: {stats['messages_sent']}\n"
                            f"Ошибок: {stats['messages_failed']}\n"
                            f"Уже отправлено ранее: {stats['already_sent']}"
                        )
                        
                        self.statusBar().showMessage("Рассылка завершена")
                        
                        # If all users received messages, ask to reset for next mailing
                        total_processed = stats['messages_sent'] + stats['already_sent']
                        if total_processed >= self.member_count:
                            reply_auto_reset = QMessageBox.question(
                                self,
                                "Рассылка завершена",
                                "Все участники получили сообщения.\n"
                                "Сбросить прогресс для следующей рассылки?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                            )
                            
                            if reply_auto_reset == QMessageBox.StandardButton.Yes:
                                try:
                                    self.progress_tracker.reset_progress(self.current_group_url)
                                    self.progress_panel.reset_progress()
                                    self.statusBar().showMessage("Прогресс сброшен")
                                except Exception as e:
                                    print(f"Error resetting progress: {e}")
                        
                    except Exception as e:
                        import traceback
                        error_details = traceback.format_exc()
                        print(f"Error in mailing: {error_details}")
                        
                        QMessageBox.critical(
                            self,
                            "Ошибка рассылки",
                            f"Произошла ошибка при рассылке:\n{str(e)}\n\n"
                            f"Проверьте файл errors.txt для подробностей."
                        )
                        self.statusBar().showMessage("Ошибка рассылки")
                    
                    finally:
                        # Re-enable start button
                        try:
                            self.progress_panel.start_mailing_btn.setEnabled(True)
                        except Exception as e:
                            print(f"Error re-enabling button: {e}")
                
                # Get or create event loop
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Run mailing
                loop.run_until_complete(run_mailing())
            
            # Use QTimer to run async code without blocking UI
            QTimer.singleShot(100, start_async_mailing)
    
    def load_window_geometry(self) -> None:
        """Load saved window geometry."""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)
    
    def save_window_geometry(self) -> None:
        """Save window geometry."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handle window close event.
        
        Shows confirmation dialog if mailing is in progress.
        Saves window geometry before closing.
        """
        # TODO: Check if mailing is in progress
        # For now, just save geometry
        
        self.save_window_geometry()
        
        # Disconnect from Telegram if connected
        if self.telegram_service and self.telegram_service.is_connected:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                loop.run_until_complete(self.telegram_service.disconnect())
            except (TypeError, AttributeError, RuntimeError):
                # Handle mocked telegram_service in tests or closed loop
                pass
        
        event.accept()


def main():
    """Main entry point for testing the window."""
    app = QApplication(sys.argv)
    
    # Set application style for MacOS
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
