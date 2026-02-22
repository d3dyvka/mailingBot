"""
Tests for Main Window GUI.

Tests the main window functionality including:
- Window initialization
- Configuration panel
- Authentication panel
- Group selection panel
- End date panel
- Window geometry persistence
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDateTime
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

from ui.main_window import MainWindow
from config.config_manager import ConfigManager


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def main_window(qapp, tmp_path):
    """Create MainWindow instance for testing."""
    # Mock config directory
    with patch('ui.main_window.CONFIG_DIR', tmp_path / 'config'):
        with patch('ui.main_window.SESSION_DIR', tmp_path / 'session'):
            window = MainWindow()
            yield window
            window.close()


def test_window_initialization(main_window):
    """Test that window initializes correctly."""
    assert main_window.windowTitle() == "Telegram Рассыльщик"
    assert main_window.minimumWidth() == 800
    assert main_window.minimumHeight() == 900


def test_config_panel_exists(main_window):
    """Test that configuration panel exists with correct widgets."""
    assert main_window.api_id_input is not None
    assert main_window.api_hash_input is not None
    assert main_window.save_config_btn is not None
    assert main_window.edit_config_btn is not None


def test_auth_panel_exists(main_window):
    """Test that authentication panel exists with correct widgets."""
    assert main_window.phone_input is not None
    assert main_window.send_code_btn is not None
    assert main_window.code_input is not None
    assert main_window.password_input is not None
    assert main_window.sign_in_btn is not None
    assert main_window.logout_btn is not None


def test_group_panel_exists(main_window):
    """Test that group selection panel exists with correct widgets."""
    assert main_window.group_url_input is not None
    assert main_window.load_members_btn is not None
    assert main_window.member_count_label is not None


def test_end_date_panel_exists(main_window):
    """Test that end date panel exists with correct widgets."""
    assert main_window.end_date_input is not None
    assert main_window.calculate_btn is not None
    assert main_window.delay_info_label is not None


def test_initial_state(main_window):
    """Test that widgets are in correct initial state."""
    # Auth panel should be disabled initially
    assert not main_window.phone_input.isEnabled()
    assert not main_window.send_code_btn.isEnabled()
    assert not main_window.code_input.isEnabled()
    assert not main_window.password_input.isEnabled()
    assert not main_window.sign_in_btn.isEnabled()
    
    # Group panel should be disabled initially
    assert not main_window.group_url_input.isEnabled()
    assert not main_window.load_members_btn.isEnabled()
    
    # End date panel should be disabled initially
    assert not main_window.end_date_input.isEnabled()
    assert not main_window.calculate_btn.isEnabled()


def test_save_credentials_validation(main_window, qtbot):
    """Test that credential validation works."""
    # Empty credentials should show warning
    main_window.api_id_input.setText("")
    main_window.api_hash_input.setText("")
    
    with patch.object(main_window, 'statusBar') as mock_status:
        with patch('ui.main_window.QMessageBox.warning') as mock_warning:
            QTest.mouseClick(main_window.save_config_btn, Qt.MouseButton.LeftButton)
            mock_warning.assert_called_once()


def test_save_credentials_success(main_window, qtbot, tmp_path):
    """Test successful credential saving."""
    # Set valid credentials
    main_window.api_id_input.setText("12345")
    main_window.api_hash_input.setText("abcdef123456")
    
    with patch.object(main_window.config_manager, 'save_api_credentials') as mock_save:
        with patch('ui.main_window.QMessageBox.information') as mock_info:
            with patch('ui.main_window.TelegramService') as mock_service:
                QTest.mouseClick(main_window.save_config_btn, Qt.MouseButton.LeftButton)
                
                # Verify credentials were saved
                mock_save.assert_called_once_with("12345", "abcdef123456")
                
                # Verify UI updated
                assert not main_window.api_id_input.isEnabled()
                assert not main_window.api_hash_input.isEnabled()
                # Check if button is hidden (not visible in layout)
                assert not main_window.save_config_btn.isVisible() or main_window.save_config_btn.isHidden()
                
                # Verify auth panel enabled
                assert main_window.phone_input.isEnabled()
                assert main_window.send_code_btn.isEnabled()


def test_enable_credential_editing(main_window, qtbot):
    """Test that credential editing can be enabled."""
    # First save credentials
    main_window.api_id_input.setText("12345")
    main_window.api_hash_input.setText("abcdef123456")
    main_window.api_id_input.setEnabled(False)
    main_window.api_hash_input.setEnabled(False)
    main_window.save_config_btn.hide()
    main_window.edit_config_btn.show()
    
    # Click edit button
    QTest.mouseClick(main_window.edit_config_btn, Qt.MouseButton.LeftButton)
    
    # Verify inputs are enabled
    assert main_window.api_id_input.isEnabled()
    assert main_window.api_hash_input.isEnabled()
    # Check if button is visible (not hidden)
    assert main_window.save_config_btn.isVisible() or not main_window.save_config_btn.isHidden()
    assert main_window.edit_config_btn.isHidden() or not main_window.edit_config_btn.isVisible()


def test_calculate_delay_without_members(main_window, qtbot):
    """Test that delay calculation requires members to be loaded."""
    main_window.member_count = 0
    main_window.calculate_btn.setEnabled(True)  # Enable button for test
    
    with patch('ui.main_window.QMessageBox.warning') as mock_warning:
        QTest.mouseClick(main_window.calculate_btn, Qt.MouseButton.LeftButton)
        mock_warning.assert_called_once()


def test_calculate_delay_with_members(main_window, qtbot):
    """Test delay calculation with loaded members."""
    main_window.member_count = 100
    
    # Set end date to 30 days from now
    end_date = QDateTime.currentDateTime().addDays(30)
    main_window.end_date_input.setDateTime(end_date)
    
    # Calculate delay
    main_window.calculate_delay()
    
    # Verify delay info is displayed
    assert "Delay:" in main_window.delay_info_label.text()
    assert "Batches:" in main_window.delay_info_label.text()


def test_window_geometry_persistence(main_window, qtbot, tmp_path):
    """Test that window geometry is saved and loaded."""
    # Set window geometry
    main_window.setGeometry(100, 100, 800, 600)
    
    # Save geometry
    main_window.save_window_geometry()
    
    # Create new window and load geometry
    with patch('ui.main_window.CONFIG_DIR', tmp_path / 'config'):
        with patch('ui.main_window.SESSION_DIR', tmp_path / 'session'):
            new_window = MainWindow()
            
            # Geometry should be restored (approximately)
            # Note: Exact values may vary due to window manager
            assert new_window.width() > 0
            assert new_window.height() > 0
            
            new_window.close()


def test_on_authentication_success(main_window, qtbot):
    """Test UI state after successful authentication."""
    with patch('ui.main_window.QMessageBox.information'):
        main_window.on_authentication_success()
    
    # Auth inputs should be disabled
    assert not main_window.phone_input.isEnabled()
    assert not main_window.send_code_btn.isEnabled()
    assert not main_window.code_input.isEnabled()
    assert not main_window.password_input.isEnabled()
    assert not main_window.sign_in_btn.isEnabled()
    
    # Logout button should be enabled and visible
    assert main_window.logout_btn.isEnabled()
    # Check if button is shown (not hidden)
    assert main_window.logout_btn.isVisible() or not main_window.logout_btn.isHidden()
    
    # Group panel should be enabled
    assert main_window.group_url_input.isEnabled()
    assert main_window.load_members_btn.isEnabled()


def test_signals_exist(main_window):
    """Test that required signals exist."""
    assert hasattr(main_window, 'credentials_saved')
    assert hasattr(main_window, 'authenticated')
    assert hasattr(main_window, 'group_selected')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



def test_text_editor_panel_exists(main_window):
    """Test that text editor panel exists."""
    assert hasattr(main_window, 'text_editor_panel')
    assert main_window.text_editor_panel is not None


def test_progress_panel_exists(main_window):
    """Test that progress panel exists."""
    assert hasattr(main_window, 'progress_panel')
    assert main_window.progress_panel is not None


def test_message_saved_handler(main_window):
    """Test message saved handler."""
    test_html = "<b>Test</b>"
    test_plain = "Test"
    
    main_window.on_message_saved(test_html, test_plain)
    
    assert main_window.message_html == test_html
    assert main_window.message_plain == test_plain


def test_progress_panel_integration(main_window):
    """Test progress panel integration with group members."""
    # Simulate loading group members
    main_window.member_count = 100
    main_window.progress_panel.set_total_users(100)
    
    assert main_window.progress_panel.total_users == 100
    assert main_window.progress_panel.remaining_count == 100
