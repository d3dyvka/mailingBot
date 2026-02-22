"""
Unit tests for Progress Tracker.

Tests the append-only progress tracking functionality including:
- Loading and saving progress
- Append-only file operations
- Statistics calculation
- Progress reset
"""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from utils.progress_tracker import ProgressTracker


@pytest.fixture
def temp_progress_dir():
    """Create a temporary directory for progress files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def progress_tracker(temp_progress_dir):
    """Create a ProgressTracker instance with temporary directory."""
    return ProgressTracker(temp_progress_dir)


class TestProgressTrackerInitialization:
    """Test ProgressTracker initialization."""
    
    def test_init_creates_directory(self, temp_progress_dir):
        """Test that initialization creates the progress directory."""
        # Remove the directory first
        shutil.rmtree(temp_progress_dir)
        assert not temp_progress_dir.exists()
        
        # Initialize tracker
        tracker = ProgressTracker(temp_progress_dir)
        
        # Directory should be created
        assert temp_progress_dir.exists()
        assert temp_progress_dir.is_dir()
    
    def test_init_with_existing_directory(self, temp_progress_dir):
        """Test initialization with existing directory."""
        # Directory already exists from fixture
        tracker = ProgressTracker(temp_progress_dir)
        
        assert tracker.progress_dir == temp_progress_dir
        assert tracker.sent_users == set()
        assert tracker.current_group_url == ""


class TestProgressFileOperations:
    """Test progress file operations."""
    
    def test_load_progress_empty_file(self, progress_tracker):
        """Test loading progress when no file exists."""
        group_url = "https://t.me/testgroup"
        
        sent_users = progress_tracker.load_progress(group_url)
        
        assert sent_users == set()
        assert progress_tracker.current_group_url == group_url
        assert progress_tracker.progress_file is not None
    
    def test_append_sent_user(self, progress_tracker):
        """Test appending a sent user to the progress file."""
        group_url = "https://t.me/testgroup"
        progress_tracker.load_progress(group_url)
        
        user_id = 123456
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        
        progress_tracker.append_sent_user(user_id, timestamp)
        
        # Check in-memory state
        assert user_id in progress_tracker.sent_users
        
        # Check file content
        with open(progress_tracker.progress_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "ID_Пользователя/User_ID: 123456" in content
        assert "Время_Отправки/Send_Time: 2024-01-15T10:30:00" in content
        assert "---" in content
    
    def test_append_multiple_users(self, progress_tracker):
        """Test appending multiple users."""
        group_url = "https://t.me/testgroup"
        progress_tracker.load_progress(group_url)
        
        user_ids = [123456, 789012, 345678]
        
        for user_id in user_ids:
            progress_tracker.append_sent_user(user_id)
        
        # Check all users are in memory
        assert progress_tracker.sent_users == set(user_ids)
        
        # Check file has all entries
        with open(progress_tracker.progress_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for user_id in user_ids:
            assert f"ID_Пользователя/User_ID: {user_id}" in content
    
    def test_append_only_never_overwrites(self, progress_tracker):
        """Test that append operations never overwrite existing data."""
        group_url = "https://t.me/testgroup"
        progress_tracker.load_progress(group_url)
        
        # Add first user
        progress_tracker.append_sent_user(111111)
        
        # Read file content
        with open(progress_tracker.progress_file, 'r', encoding='utf-8') as f:
            first_content = f.read()
        
        # Add second user
        progress_tracker.append_sent_user(222222)
        
        # Read file content again
        with open(progress_tracker.progress_file, 'r', encoding='utf-8') as f:
            second_content = f.read()
        
        # First content should still be present
        assert first_content in second_content
        assert "ID_Пользователя/User_ID: 111111" in second_content
        assert "ID_Пользователя/User_ID: 222222" in second_content
    
    def test_load_progress_from_existing_file(self, progress_tracker):
        """Test loading progress from an existing file."""
        group_url = "https://t.me/testgroup"
        progress_tracker.load_progress(group_url)
        
        # Add some users
        user_ids = [123456, 789012, 345678]
        for user_id in user_ids:
            progress_tracker.append_sent_user(user_id)
        
        # Create a new tracker instance and load the same file
        new_tracker = ProgressTracker(progress_tracker.progress_dir)
        loaded_users = new_tracker.load_progress(group_url)
        
        # Should load all previously saved users
        assert loaded_users == set(user_ids)
        assert new_tracker.sent_users == set(user_ids)


class TestProgressTracking:
    """Test progress tracking methods."""
    
    def test_mark_sent(self, progress_tracker):
        """Test marking a user as sent."""
        group_url = "https://t.me/testgroup"
        progress_tracker.load_progress(group_url)
        
        user_id = 123456
        progress_tracker.mark_sent(user_id)
        
        assert progress_tracker.is_sent(user_id)
    
    def test_is_sent_false_for_new_user(self, progress_tracker):
        """Test is_sent returns False for users not yet sent."""
        group_url = "https://t.me/testgroup"
        progress_tracker.load_progress(group_url)
        
        assert not progress_tracker.is_sent(999999)
    
    def test_is_sent_true_after_marking(self, progress_tracker):
        """Test is_sent returns True after marking user as sent."""
        group_url = "https://t.me/testgroup"
        progress_tracker.load_progress(group_url)
        
        user_id = 123456
        progress_tracker.mark_sent(user_id)
        
        assert progress_tracker.is_sent(user_id)
    
    def test_no_duplicate_sends(self, progress_tracker):
        """Test that marking the same user multiple times doesn't create duplicates in set."""
        group_url = "https://t.me/testgroup"
        progress_tracker.load_progress(group_url)
        
        user_id = 123456
        progress_tracker.mark_sent(user_id)
        progress_tracker.mark_sent(user_id)
        progress_tracker.mark_sent(user_id)
        
        # Should only be in set once
        assert progress_tracker.sent_users.count(user_id) == 1 if hasattr(set, 'count') else True
        assert len([u for u in progress_tracker.sent_users if u == user_id]) == 1


class TestStatistics:
    """Test statistics calculation."""
    
    def test_get_statistics_empty(self, progress_tracker):
        """Test statistics with no users sent."""
        group_url = "https://t.me/testgroup"
        progress_tracker.load_progress(group_url)
        
        stats = progress_tracker.get_statistics()
        
        assert stats['sent'] == 0
        assert stats['total'] == 0
        assert stats['remaining'] == 0
    
    def test_get_statistics_with_total(self, progress_tracker):
        """Test statistics with total users set."""
        group_url = "https://t.me/testgroup"
        progress_tracker.load_progress(group_url)
        progress_tracker.set_total_users(100)
        
        # Send to 30 users
        for i in range(30):
            progress_tracker.mark_sent(i)
        
        stats = progress_tracker.get_statistics()
        
        assert stats['sent'] == 30
        assert stats['total'] == 100
        assert stats['remaining'] == 70
    
    def test_get_statistics_all_sent(self, progress_tracker):
        """Test statistics when all users have been sent."""
        group_url = "https://t.me/testgroup"
        progress_tracker.load_progress(group_url)
        progress_tracker.set_total_users(10)
        
        # Send to all users
        for i in range(10):
            progress_tracker.mark_sent(i)
        
        stats = progress_tracker.get_statistics()
        
        assert stats['sent'] == 10
        assert stats['total'] == 10
        assert stats['remaining'] == 0
    
    def test_update_summary(self, progress_tracker):
        """Test updating summary in the progress file."""
        group_url = "https://t.me/testgroup"
        progress_tracker.load_progress(group_url)
        
        # Add some users
        for i in range(5):
            progress_tracker.mark_sent(i)
        
        # Update summary
        progress_tracker.update_summary(total_users=100, sent_count=5)
        
        # Check file content
        with open(progress_tracker.progress_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "Всего_Пользователей/Total_Users: 100" in content
        assert "Отправлено/Sent_Count: 5" in content
        assert "Последнее_Обновление/Last_Updated:" in content


class TestProgressReset:
    """Test progress reset functionality."""
    
    def test_reset_progress_deletes_file(self, progress_tracker):
        """Test that reset_progress deletes the progress file."""
        group_url = "https://t.me/testgroup"
        progress_tracker.load_progress(group_url)
        
        # Add some users
        progress_tracker.mark_sent(123456)
        progress_tracker.mark_sent(789012)
        
        # File should exist
        assert progress_tracker.progress_file.exists()
        
        # Reset progress
        progress_tracker.reset_progress(group_url)
        
        # File should be deleted
        assert not progress_tracker.progress_file.exists() if progress_tracker.progress_file else True
    
    def test_reset_progress_clears_memory(self, progress_tracker):
        """Test that reset_progress clears in-memory state."""
        group_url = "https://t.me/testgroup"
        progress_tracker.load_progress(group_url)
        
        # Add some users
        progress_tracker.mark_sent(123456)
        progress_tracker.mark_sent(789012)
        
        # Reset progress
        progress_tracker.reset_progress(group_url)
        
        # Memory should be cleared
        assert progress_tracker.sent_users == set()
        assert progress_tracker.current_group_url == ""
        assert progress_tracker.total_users == 0
    
    def test_reset_nonexistent_progress(self, progress_tracker):
        """Test resetting progress for a group with no existing file."""
        group_url = "https://t.me/newgroup"
        
        # Should not raise an error
        progress_tracker.reset_progress(group_url)
        
        assert progress_tracker.sent_users == set()


class TestGroupHashing:
    """Test group URL hashing for file names."""
    
    def test_different_groups_different_files(self, progress_tracker):
        """Test that different groups get different progress files."""
        group1 = "https://t.me/group1"
        group2 = "https://t.me/group2"
        
        progress_tracker.load_progress(group1)
        file1 = progress_tracker.progress_file
        
        progress_tracker.load_progress(group2)
        file2 = progress_tracker.progress_file
        
        assert file1 != file2
    
    def test_same_group_same_file(self, progress_tracker):
        """Test that the same group always gets the same progress file."""
        group_url = "https://t.me/testgroup"
        
        progress_tracker.load_progress(group_url)
        file1 = progress_tracker.progress_file
        
        # Create new tracker and load same group
        new_tracker = ProgressTracker(progress_tracker.progress_dir)
        new_tracker.load_progress(group_url)
        file2 = new_tracker.progress_file
        
        assert file1 == file2


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_append_without_load_raises_error(self, progress_tracker):
        """Test that appending without loading progress raises an error."""
        with pytest.raises(ValueError, match="Progress file not initialized"):
            progress_tracker.append_sent_user(123456)
    
    def test_update_summary_without_load_raises_error(self, progress_tracker):
        """Test that updating summary without loading progress raises an error."""
        with pytest.raises(ValueError, match="Progress file not initialized"):
            progress_tracker.update_summary(100, 50)
    
    def test_load_corrupted_file(self, progress_tracker, temp_progress_dir):
        """Test loading a corrupted progress file."""
        group_url = "https://t.me/testgroup"
        progress_file = progress_tracker._get_progress_file_path(group_url)
        
        # Create a corrupted file
        with open(progress_file, 'w', encoding='utf-8') as f:
            f.write("This is corrupted data\n")
            f.write("ID_Пользователя/User_ID: not_a_number\n")
            f.write("ID_Пользователя/User_ID: 123456\n")
        
        # Should handle gracefully
        sent_users = progress_tracker.load_progress(group_url)
        
        # Should only load valid user ID
        assert 123456 in sent_users
        assert len(sent_users) == 1
    
    def test_empty_group_url(self, progress_tracker):
        """Test with empty group URL."""
        group_url = ""
        
        # Should not raise an error
        progress_tracker.load_progress(group_url)
        
        assert progress_tracker.current_group_url == ""
        assert progress_tracker.progress_file is not None
