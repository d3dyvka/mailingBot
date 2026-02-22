"""
Unit tests for Progress Panel.

Tests the progress tracking functionality including:
- Progress bar updates
- Counter updates (sent/remaining/failed)
- Countdown timer
- Reset and logout functionality
"""

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from ui.progress_panel import ProgressPanel


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def progress_panel(qapp):
    """Create ProgressPanel instance for testing."""
    panel = ProgressPanel()
    yield panel
    panel.deleteLater()


class TestProgressPanel:
    """Test suite for ProgressPanel."""
    
    def test_initialization(self, progress_panel):
        """Test that panel initializes correctly."""
        assert progress_panel.progress_bar is not None
        assert progress_panel.sent_label is not None
        assert progress_panel.remaining_label is not None
        assert progress_panel.failed_label is not None
        assert progress_panel.countdown_label is not None
        assert progress_panel.start_mailing_btn is not None
        assert progress_panel.reset_btn is not None
        assert progress_panel.logout_btn is not None
        
        # Initial values
        assert progress_panel.total_users == 0
        assert progress_panel.sent_count == 0
        assert progress_panel.failed_count == 0
        assert progress_panel.remaining_count == 0
    
    def test_set_total_users(self, progress_panel):
        """Test setting total users."""
        progress_panel.set_total_users(100)
        
        assert progress_panel.total_users == 100
        assert progress_panel.remaining_count == 100
        assert progress_panel.remaining_label.text() == "100"
    
    def test_update_progress(self, progress_panel):
        """Test updating progress counters."""
        progress_panel.set_total_users(100)
        progress_panel.update_progress(sent=30, failed=5)
        
        assert progress_panel.sent_count == 30
        assert progress_panel.failed_count == 5
        assert progress_panel.remaining_count == 65
        
        assert progress_panel.sent_label.text() == "30"
        assert progress_panel.failed_label.text() == "5"
        assert progress_panel.remaining_label.text() == "65"
    
    def test_increment_sent(self, progress_panel):
        """Test incrementing sent counter."""
        progress_panel.set_total_users(100)
        progress_panel.update_progress(sent=10, failed=0)
        
        progress_panel.increment_sent()
        
        assert progress_panel.sent_count == 11
        assert progress_panel.remaining_count == 89
    
    def test_increment_failed(self, progress_panel):
        """Test incrementing failed counter."""
        progress_panel.set_total_users(100)
        progress_panel.update_progress(sent=10, failed=2)
        
        progress_panel.increment_failed()
        
        assert progress_panel.failed_count == 3
        assert progress_panel.remaining_count == 87
    
    def test_progress_bar_percentage(self, progress_panel):
        """Test progress bar percentage calculation."""
        progress_panel.set_total_users(100)
        progress_panel.update_progress(sent=50, failed=10)
        
        # 60 out of 100 = 60%
        assert progress_panel.progress_bar.value() == 60
    
    def test_progress_bar_zero_users(self, progress_panel):
        """Test progress bar with zero users."""
        progress_panel.set_total_users(0)
        progress_panel.update_progress(sent=0, failed=0)
        
        assert progress_panel.progress_bar.value() == 0
    
    def test_progress_bar_complete(self, progress_panel):
        """Test progress bar at 100%."""
        progress_panel.set_total_users(100)
        progress_panel.update_progress(sent=90, failed=10)
        
        # All users processed
        assert progress_panel.progress_bar.value() == 100
    
    def test_countdown_timer_start(self, progress_panel):
        """Test starting countdown timer."""
        progress_panel.start_countdown(3600, "Waiting between batches")
        
        # Timer should be active and countdown should be close to 3600
        # (may have decremented by 1 due to timing)
        assert progress_panel.countdown_timer.isActive()
        assert progress_panel.countdown_seconds >= 3599
        assert "01:00:0" in progress_panel.countdown_label.text()  # Should show 01:00:00 or 01:00:01
    
    def test_countdown_timer_stop(self, progress_panel):
        """Test stopping countdown timer."""
        progress_panel.start_countdown(100, "Test")
        progress_panel.stop_countdown()
        
        assert progress_panel.countdown_seconds == 0
        assert not progress_panel.countdown_timer.isActive()
        assert progress_panel.countdown_label.text() == "Задержка не активна"
    
    def test_countdown_formatting(self, progress_panel):
        """Test countdown time formatting."""
        # Test various time formats
        test_cases = [
            (3661, "01:01:01"),  # 1 hour, 1 minute, 1 second
            (3600, "01:00:00"),  # 1 hour
            (60, "00:01:00"),    # 1 minute
            (1, "00:00:01"),     # 1 second
        ]
        
        for seconds, expected in test_cases:
            progress_panel.start_countdown(seconds, "Test")
            assert expected in progress_panel.countdown_label.text()
            progress_panel.stop_countdown()
    
    def test_get_remaining_countdown(self, progress_panel):
        """Test getting remaining countdown seconds."""
        progress_panel.start_countdown(100, "Test")
        
        remaining = progress_panel.get_remaining_countdown()
        # Should be close to 100 (may have decremented by 1 due to timing)
        assert remaining >= 99
        
        progress_panel.stop_countdown()
    
    def test_reset_progress(self, progress_panel):
        """Test resetting progress."""
        progress_panel.set_total_users(100)
        progress_panel.update_progress(sent=50, failed=10)
        progress_panel.start_countdown(100, "Test")
        
        progress_panel.reset_progress()
        
        assert progress_panel.sent_count == 0
        assert progress_panel.failed_count == 0
        assert progress_panel.remaining_count == 100
        assert progress_panel.progress_bar.value() == 0
        assert not progress_panel.countdown_timer.isActive()
    
    def test_get_statistics(self, progress_panel):
        """Test getting progress statistics."""
        progress_panel.set_total_users(100)
        progress_panel.update_progress(sent=30, failed=5)
        
        stats = progress_panel.get_statistics()
        
        assert stats['sent'] == 30
        assert stats['failed'] == 5
        assert stats['remaining'] == 65
        assert stats['total'] == 100
        assert stats['percentage'] == 35  # (30 + 5) / 100 * 100
    
    def test_set_buttons_enabled(self, progress_panel):
        """Test enabling/disabling buttons."""
        progress_panel.set_buttons_enabled(False)
        
        assert not progress_panel.start_mailing_btn.isEnabled()
        assert not progress_panel.reset_btn.isEnabled()
        assert not progress_panel.logout_btn.isEnabled()
        
        progress_panel.set_buttons_enabled(True)
        
        assert progress_panel.start_mailing_btn.isEnabled()
        assert progress_panel.reset_btn.isEnabled()
        assert progress_panel.logout_btn.isEnabled()
    
    def test_reset_progress_signal(self, progress_panel, qtbot, monkeypatch):
        """Test that reset_progress_clicked signal is emitted."""
        progress_panel.set_total_users(100)
        
        # Mock QMessageBox to auto-accept
        from PyQt6.QtWidgets import QMessageBox
        monkeypatch.setattr(QMessageBox, 'question', lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
        
        with qtbot.waitSignal(progress_panel.reset_progress_clicked, timeout=1000):
            progress_panel.reset_btn.click()
    
    def test_logout_signal(self, progress_panel, qtbot):
        """Test that logout_clicked signal is emitted."""
        with qtbot.waitSignal(progress_panel.logout_clicked, timeout=1000):
            progress_panel.logout_btn.click()
    
    def test_start_mailing_signal(self, progress_panel, qtbot):
        """Test that start_mailing_clicked signal is emitted."""
        with qtbot.waitSignal(progress_panel.start_mailing_clicked, timeout=1000):
            progress_panel.start_mailing_btn.click()
    
    def test_countdown_auto_stop(self, progress_panel, qtbot):
        """Test that countdown stops automatically when reaching zero."""
        progress_panel.start_countdown(1, "Test")
        
        # Wait for countdown to finish (1 second + buffer)
        qtbot.wait(1500)
        
        assert not progress_panel.countdown_timer.isActive()
        assert progress_panel.countdown_label.text() == "Задержка не активна"
    
    def test_remaining_count_never_negative(self, progress_panel):
        """Test that remaining count never goes negative."""
        progress_panel.set_total_users(10)
        progress_panel.update_progress(sent=8, failed=5)  # Total > total_users
        
        # Remaining should be 0, not negative
        assert progress_panel.remaining_count >= 0
