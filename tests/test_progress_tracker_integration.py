"""
Integration tests for Progress Tracker.

Tests real-world scenarios and integration with the mailing workflow.
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


class TestMailingWorkflow:
    """Test realistic mailing workflow scenarios."""
    
    def test_complete_mailing_workflow(self, temp_progress_dir):
        """Test a complete mailing workflow from start to finish."""
        tracker = ProgressTracker(temp_progress_dir)
        group_url = "https://t.me/testgroup"
        
        # Step 1: Start new mailing campaign
        tracker.load_progress(group_url)
        tracker.set_total_users(50)
        
        # Step 2: Send messages in batches
        batch1 = list(range(1, 19))  # 18 users
        for user_id in batch1:
            tracker.mark_sent(user_id)
        
        stats = tracker.get_statistics()
        assert stats['sent'] == 18
        assert stats['remaining'] == 32
        
        # Step 3: Simulate app restart - create new tracker
        tracker2 = ProgressTracker(temp_progress_dir)
        tracker2.load_progress(group_url)
        tracker2.set_total_users(50)
        
        # Should remember previous progress
        assert len(tracker2.sent_users) == 18
        for user_id in batch1:
            assert tracker2.is_sent(user_id)
        
        # Step 4: Continue with second batch
        batch2 = list(range(19, 37))  # Another 18 users
        for user_id in batch2:
            tracker2.mark_sent(user_id)
        
        stats = tracker2.get_statistics()
        assert stats['sent'] == 36
        assert stats['remaining'] == 14
        
        # Step 5: Final batch
        batch3 = list(range(37, 51))  # Remaining 14 users
        for user_id in batch3:
            tracker2.mark_sent(user_id)
        
        stats = tracker2.get_statistics()
        assert stats['sent'] == 50
        assert stats['remaining'] == 0
        
        # Step 6: Update summary
        tracker2.update_summary(total_users=50, sent_count=50)
        
        # Verify file content
        with open(tracker2.progress_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "Всего_Пользователей/Total_Users: 50" in content
        assert "Отправлено/Sent_Count: 50" in content
    
    def test_resume_after_crash(self, temp_progress_dir):
        """Test resuming mailing after application crash."""
        tracker = ProgressTracker(temp_progress_dir)
        group_url = "https://t.me/testgroup"
        
        # Start mailing
        tracker.load_progress(group_url)
        tracker.set_total_users(100)
        
        # Send to first 30 users
        for i in range(1, 31):
            tracker.mark_sent(i)
        
        # Simulate crash - don't call any cleanup
        del tracker
        
        # Restart application
        new_tracker = ProgressTracker(temp_progress_dir)
        new_tracker.load_progress(group_url)
        new_tracker.set_total_users(100)
        
        # Should have all previous progress
        assert len(new_tracker.sent_users) == 30
        
        # Continue from where we left off
        for i in range(31, 61):
            new_tracker.mark_sent(i)
        
        stats = new_tracker.get_statistics()
        assert stats['sent'] == 60
        assert stats['remaining'] == 40
    
    def test_skip_already_sent_users(self, temp_progress_dir):
        """Test that already-sent users are skipped in resumed mailing."""
        tracker = ProgressTracker(temp_progress_dir)
        group_url = "https://t.me/testgroup"
        
        # Initial mailing
        tracker.load_progress(group_url)
        sent_users = [1, 2, 3, 4, 5]
        for user_id in sent_users:
            tracker.mark_sent(user_id)
        
        # Resume mailing
        tracker2 = ProgressTracker(temp_progress_dir)
        tracker2.load_progress(group_url)
        
        # Simulate checking users before sending
        all_users = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        users_to_send = [u for u in all_users if not tracker2.is_sent(u)]
        
        # Should only include users 6-10
        assert users_to_send == [6, 7, 8, 9, 10]
        
        # Send to remaining users
        for user_id in users_to_send:
            tracker2.mark_sent(user_id)
        
        # All users should now be marked as sent
        for user_id in all_users:
            assert tracker2.is_sent(user_id)
    
    def test_multiple_groups_independent_progress(self, temp_progress_dir):
        """Test that different groups maintain independent progress."""
        tracker = ProgressTracker(temp_progress_dir)
        
        group1 = "https://t.me/group1"
        group2 = "https://t.me/group2"
        
        # Send to users in group1
        tracker.load_progress(group1)
        for i in range(1, 11):
            tracker.mark_sent(i)
        
        # Send to users in group2
        tracker.load_progress(group2)
        for i in range(101, 111):
            tracker.mark_sent(i)
        
        # Verify group1 progress
        tracker.load_progress(group1)
        assert len(tracker.sent_users) == 10
        assert tracker.is_sent(5)
        assert not tracker.is_sent(105)
        
        # Verify group2 progress
        tracker.load_progress(group2)
        assert len(tracker.sent_users) == 10
        assert tracker.is_sent(105)
        assert not tracker.is_sent(5)
    
    def test_append_only_preserves_history(self, temp_progress_dir):
        """Test that append-only logic preserves complete history."""
        tracker = ProgressTracker(temp_progress_dir)
        group_url = "https://t.me/testgroup"
        
        tracker.load_progress(group_url)
        
        # Send messages at different times
        timestamps = [
            datetime(2024, 1, 15, 10, 0, 0),
            datetime(2024, 1, 15, 10, 30, 0),
            datetime(2024, 1, 15, 11, 0, 0),
        ]
        
        user_ids = [111, 222, 333]
        
        for user_id, timestamp in zip(user_ids, timestamps):
            tracker.append_sent_user(user_id, timestamp)
        
        # Read file and verify all timestamps are preserved
        with open(tracker.progress_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "2024-01-15T10:00:00" in content
        assert "2024-01-15T10:30:00" in content
        assert "2024-01-15T11:00:00" in content
        
        # Verify all user IDs are present
        for user_id in user_ids:
            assert f"ID_Пользователя/User_ID: {user_id}" in content
    
    def test_bilingual_format(self, temp_progress_dir):
        """Test that progress file uses bilingual format (Russian/English)."""
        tracker = ProgressTracker(temp_progress_dir)
        group_url = "https://t.me/testgroup"
        
        tracker.load_progress(group_url)
        tracker.mark_sent(123456)
        tracker.update_summary(total_users=100, sent_count=1)
        
        # Read file and verify bilingual format
        with open(tracker.progress_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check bilingual field names
        assert "ID_Пользователя/User_ID:" in content
        assert "Время_Отправки/Send_Time:" in content
        assert "Всего_Пользователей/Total_Users:" in content
        assert "Отправлено/Sent_Count:" in content
        assert "Последнее_Обновление/Last_Updated:" in content


class TestErrorRecovery:
    """Test error recovery scenarios."""
    
    def test_recover_from_partial_write(self, temp_progress_dir):
        """Test recovery from partial file write (simulated crash during write)."""
        tracker = ProgressTracker(temp_progress_dir)
        group_url = "https://t.me/testgroup"
        
        tracker.load_progress(group_url)
        
        # Write some complete entries
        tracker.mark_sent(111)
        tracker.mark_sent(222)
        
        # Manually append incomplete entry (simulating crash)
        with open(tracker.progress_file, 'a', encoding='utf-8') as f:
            f.write("ID_Пользователя/User_ID: 333\n")
            # Missing timestamp and separator
        
        # Load progress again
        tracker2 = ProgressTracker(temp_progress_dir)
        tracker2.load_progress(group_url)
        
        # Should recover the complete entries
        assert tracker2.is_sent(111)
        assert tracker2.is_sent(222)
        assert tracker2.is_sent(333)  # Partial entry should still be loaded
    
    def test_file_permissions_preserved(self, temp_progress_dir):
        """Test that file permissions are appropriate for progress files."""
        tracker = ProgressTracker(temp_progress_dir)
        group_url = "https://t.me/testgroup"
        
        tracker.load_progress(group_url)
        tracker.mark_sent(123456)
        
        # Check that file exists and is readable/writable
        assert tracker.progress_file.exists()
        assert tracker.progress_file.is_file()
        
        # File should be readable and writable
        with open(tracker.progress_file, 'r') as f:
            content = f.read()
            assert len(content) > 0
