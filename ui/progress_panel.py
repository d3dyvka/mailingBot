"""
Progress Panel for Telegram Mailer MacOS App.

Provides real-time progress tracking for mailing campaigns:
- Progress bar showing completion percentage
- Counters for sent/remaining/failed messages
- Countdown timer for batch delays
- Reset progress and logout buttons
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QProgressBar,
    QLabel,
    QPushButton,
    QGroupBox,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer


class ProgressPanel(QWidget):
    """
    Progress panel for mailing campaign tracking.
    
    Provides:
    - Progress bar with percentage
    - Sent/Remaining/Failed counters
    - Countdown timer for delays
    - Reset and Logout buttons
    
    Signals:
        reset_progress_clicked: Emitted when reset progress button is clicked
        logout_clicked: Emitted when logout button is clicked
    """
    
    reset_progress_clicked = pyqtSignal()
    logout_clicked = pyqtSignal()
    start_mailing_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize the progress panel."""
        super().__init__(parent)
        
        # Progress tracking
        self.total_users = 0
        self.sent_count = 0
        self.failed_count = 0
        self.remaining_count = 0
        
        # Timer for countdown
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self._update_countdown)
        self.countdown_seconds = 0
        
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Progress group
        progress_group = QGroupBox("Прогресс рассылки")
        progress_group.setMinimumHeight(140)
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(15)
        progress_layout.setContentsMargins(10, 15, 10, 15)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% Завершено")
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e1e8ed;
                border-radius: 6px;
                text-align: center;
                background-color: #ecf0f1;
                color: #2c3e50;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 4px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        # Counters - simple horizontal layout
        counters_layout = QHBoxLayout()
        counters_layout.setSpacing(40)
        counters_layout.setContentsMargins(20, 5, 20, 5)
        
        # Sent counter
        sent_layout = QVBoxLayout()
        sent_layout.setSpacing(5)
        self.sent_label = QLabel("0")
        self.sent_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #27ae60;")
        self.sent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sent_label.setMinimumHeight(28)
        sent_title = QLabel("Отправлено")
        sent_title.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        sent_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sent_layout.addWidget(self.sent_label)
        sent_layout.addWidget(sent_title)
        counters_layout.addLayout(sent_layout)
        
        # Remaining counter
        remaining_layout = QVBoxLayout()
        remaining_layout.setSpacing(5)
        self.remaining_label = QLabel("0")
        self.remaining_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #3498db;")
        self.remaining_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.remaining_label.setMinimumHeight(28)
        remaining_title = QLabel("Осталось")
        remaining_title.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        remaining_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        remaining_layout.addWidget(self.remaining_label)
        remaining_layout.addWidget(remaining_title)
        counters_layout.addLayout(remaining_layout)
        
        # Failed counter
        failed_layout = QVBoxLayout()
        failed_layout.setSpacing(5)
        self.failed_label = QLabel("0")
        self.failed_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #e74c3c;")
        self.failed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.failed_label.setMinimumHeight(28)
        failed_title = QLabel("Ошибки")
        failed_title.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        failed_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        failed_layout.addWidget(self.failed_label)
        failed_layout.addWidget(failed_title)
        counters_layout.addLayout(failed_layout)
        
        progress_layout.addLayout(counters_layout)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Countdown group
        countdown_group = QGroupBox("Обратный отсчет задержки")
        countdown_group.setMinimumHeight(90)
        countdown_layout = QVBoxLayout()
        countdown_layout.setSpacing(5)
        countdown_layout.setContentsMargins(15, 15, 15, 15)
        
        # Countdown display
        self.countdown_label = QLabel("Задержка не активна")
        self.countdown_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setMinimumHeight(30)
        countdown_layout.addWidget(self.countdown_label)
        
        # Reason display
        self.countdown_reason_label = QLabel("")
        self.countdown_reason_label.setStyleSheet("font-size: 12px; color: #666;")
        self.countdown_reason_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_reason_label.setWordWrap(True)
        self.countdown_reason_label.setMinimumHeight(20)
        countdown_layout.addWidget(self.countdown_reason_label)
        
        countdown_group.setLayout(countdown_layout)
        layout.addWidget(countdown_group)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.start_mailing_btn = QPushButton("Начать рассылку")
        self.start_mailing_btn.setMinimumHeight(40)
        self.start_mailing_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.start_mailing_btn.clicked.connect(self._on_start_mailing_clicked)
        buttons_layout.addWidget(self.start_mailing_btn)
        
        self.reset_btn = QPushButton("Сбросить прогресс")
        self.reset_btn.setMinimumHeight(40)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                font-weight: 500;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        self.reset_btn.clicked.connect(self._on_reset_clicked)
        buttons_layout.addWidget(self.reset_btn)
        
        self.logout_btn = QPushButton("Выйти")
        self.logout_btn.setMinimumHeight(40)
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-weight: 500;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.logout_btn.clicked.connect(self._on_logout_clicked)
        buttons_layout.addWidget(self.logout_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def set_total_users(self, total: int) -> None:
        """
        Set total number of users for progress tracking.
        
        Args:
            total: Total number of users
        """
        self.total_users = total
        self.remaining_count = total
        self.remaining_label.setText(str(total))
        self._update_progress_bar()
    
    def update_progress(self, sent: int, failed: int) -> None:
        """
        Update progress counters.
        
        Args:
            sent: Number of messages sent successfully
            failed: Number of messages failed
        """
        self.sent_count = sent
        self.failed_count = failed
        self.remaining_count = max(0, self.total_users - sent - failed)
        
        # Update labels
        self.sent_label.setText(str(sent))
        self.failed_label.setText(str(failed))
        self.remaining_label.setText(str(self.remaining_count))
        
        # Update progress bar
        self._update_progress_bar()
    
    def increment_sent(self) -> None:
        """Increment sent counter by 1."""
        self.update_progress(self.sent_count + 1, self.failed_count)
    
    def increment_failed(self) -> None:
        """Increment failed counter by 1."""
        self.update_progress(self.sent_count, self.failed_count + 1)
    
    def _update_progress_bar(self) -> None:
        """Update progress bar based on current counts."""
        if self.total_users > 0:
            processed = self.sent_count + self.failed_count
            percentage = int((processed / self.total_users) * 100)
            self.progress_bar.setValue(percentage)
        else:
            self.progress_bar.setValue(0)
    
    def start_countdown(self, seconds: int, reason: str = "Ожидание между батчами") -> None:
        """
        Start countdown timer.
        
        Args:
            seconds: Number of seconds to count down
            reason: Reason for the delay (displayed to user)
        """
        self.countdown_seconds = seconds
        self.countdown_reason_label.setText(reason)
        
        # Update display immediately
        self._update_countdown()
        
        # Start timer (update every second)
        self.countdown_timer.start(1000)
    
    def stop_countdown(self) -> None:
        """Stop countdown timer."""
        self.countdown_timer.stop()
        self.countdown_label.setText("Задержка не активна")
        self.countdown_reason_label.setText("")
        self.countdown_seconds = 0
    
    def _update_countdown(self) -> None:
        """Update countdown display."""
        if self.countdown_seconds <= 0:
            self.stop_countdown()
            return
        
        # Format time as HH:MM:SS
        hours = self.countdown_seconds // 3600
        minutes = (self.countdown_seconds % 3600) // 60
        seconds = self.countdown_seconds % 60
        
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.countdown_label.setText(time_str)
        
        # Decrement
        self.countdown_seconds -= 1
    
    def get_remaining_countdown(self) -> int:
        """
        Get remaining countdown seconds.
        
        Returns:
            Remaining seconds in countdown
        """
        return self.countdown_seconds
    
    def reset_progress(self) -> None:
        """Reset all progress counters and stop countdown."""
        self.sent_count = 0
        self.failed_count = 0
        self.remaining_count = self.total_users
        
        self.sent_label.setText("0")
        self.failed_label.setText("0")
        self.remaining_label.setText(str(self.total_users))
        
        self.progress_bar.setValue(0)
        self.stop_countdown()
    
    def _on_reset_clicked(self) -> None:
        """Handle reset button click."""
        reply = QMessageBox.question(
            self,
            "Подтверждение сброса",
            "Вы уверены, что хотите сбросить прогресс? Это очистит все данные отслеживания.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.reset_progress_clicked.emit()
    
    def _on_logout_clicked(self) -> None:
        """Handle logout button click."""
        self.logout_clicked.emit()
    
    def _on_start_mailing_clicked(self) -> None:
        """Handle start mailing button click."""
        self.start_mailing_clicked.emit()
    
    def set_buttons_enabled(self, enabled: bool) -> None:
        """
        Enable or disable buttons.
        
        Args:
            enabled: Whether buttons should be enabled
        """
        self.start_mailing_btn.setEnabled(enabled)
        self.reset_btn.setEnabled(enabled)
        self.logout_btn.setEnabled(enabled)
    
    def get_statistics(self) -> dict:
        """
        Get current progress statistics.
        
        Returns:
            Dictionary with sent, failed, remaining, total counts
        """
        return {
            'sent': self.sent_count,
            'failed': self.failed_count,
            'remaining': self.remaining_count,
            'total': self.total_users,
            'percentage': self.progress_bar.value()
        }
