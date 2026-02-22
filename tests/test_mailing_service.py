"""
Unit tests for MailingService.

Tests the main mailing loop coordination including:
- Batch splitting
- User filtering (skip already sent)
- Message sending with delays
- FloodWait handling
- Progress tracking integration
- Error logging integration
- Power management integration
- Resume capability
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, call
import tempfile
import shutil

from telegram.mailing_service import MailingService
from telegram.telegram_service import TelegramService
from telegram.models import User, SendResult
from utils.progress_tracker import ProgressTracker
from utils.delay_calculator import DelayCalculator
from utils.error_logger import ErrorLogger
from utils.power_manager import PowerManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_telegram_service():
    """Create a mock TelegramService."""
    service = Mock(spec=TelegramService)
    service.send_message = AsyncMock()
    return service


@pytest.fixture
def progress_tracker(temp_dir):
    """Create a real ProgressTracker with temp directory."""
    return ProgressTracker(temp_dir)


@pytest.fixture
def delay_calculator():
    """Create a real DelayCalculator."""
    return DelayCalculator(batch_size=18)


@pytest.fixture
def error_logger(temp_dir):
    """Create a real ErrorLogger with temp directory."""
    return ErrorLogger(temp_dir)


@pytest.fixture
def mock_power_manager():
    """Create a mock PowerManager."""
    manager = Mock(spec=PowerManager)
    manager.prevent_sleep = Mock()
    manager.allow_sleep = Mock()
    manager.is_sleep_prevented = Mock(return_value=False)
    return manager


@pytest.fixture
def mailing_service(
    mock_telegram_service,
    progress_tracker,
    delay_calculator,
    error_logger,
    mock_power_manager
):
    """Create a MailingService with mocked dependencies."""
    return MailingService(
        telegram_service=mock_telegram_service,
        progress_tracker=progress_tracker,
        delay_calculator=delay_calculator,
        error_logger=error_logger,
        power_manager=mock_power_manager,
        batch_size=18
    )


@pytest.fixture
def sample_users():
    """Create a list of sample users."""
    users = []
    for i in range(50):
        user = User(
            id=1000 + i,
            username=f"user{i}",
            first_name=f"User{i}",
            last_name=f"Last{i}",
            sent=False
        )
        users.append(user)
    return users


class TestBatchSplitting:
    """Tests for batch splitting functionality."""
    
    def test_split_into_batches_exact_multiple(self, mailing_service):
        """Test splitting when user count is exact multiple of batch size."""
        users = [User(id=i, username=f"user{i}", first_name=f"User{i}", last_name=None) 
                 for i in range(36)]
        
        batches = mailing_service._split_into_batches(users)
        
        assert len(batches) == 2
        assert len(batches[0]) == 18
        assert len(batches[1]) == 18
    
    def test_split_into_batches_with_remainder(self, mailing_service):
        """Test splitting when user count is not exact multiple."""
        users = [User(id=i, username=f"user{i}", first_name=f"User{i}", last_name=None) 
                 for i in range(50)]
        
        batches = mailing_service._split_into_batches(users)
        
        assert len(batches) == 3
        assert len(batches[0]) == 18
        assert len(batches[1]) == 18
        assert len(batches[2]) == 14  # Remainder
    
    def test_split_into_batches_less_than_batch_size(self, mailing_service):
        """Test splitting when user count is less than batch size."""
        users = [User(id=i, username=f"user{i}", first_name=f"User{i}", last_name=None) 
                 for i in range(10)]
        
        batches = mailing_service._split_into_batches(users)
        
        assert len(batches) == 1
        assert len(batches[0]) == 10
    
    def test_split_into_batches_empty_list(self, mailing_service):
        """Test splitting empty user list."""
        users = []
        
        batches = mailing_service._split_into_batches(users)
        
        assert len(batches) == 0


class TestUserFiltering:
    """Tests for filtering already-sent users."""
    
    @pytest.mark.asyncio
    async def test_filter_unsent_users_none_sent(self, mailing_service, sample_users):
        """Test filtering when no users have been sent messages."""
        mailing_service.progress_tracker.load_progress("https://t.me/testgroup")
        
        unsent = mailing_service._filter_unsent_users(sample_users)
        
        assert len(unsent) == len(sample_users)
        assert unsent == sample_users
    
    @pytest.mark.asyncio
    async def test_filter_unsent_users_some_sent(self, mailing_service, sample_users):
        """Test filtering when some users have been sent messages."""
        mailing_service.progress_tracker.load_progress("https://t.me/testgroup")
        
        # Mark some users as sent
        for i in range(10):
            mailing_service.progress_tracker.mark_sent(sample_users[i].id)
        
        unsent = mailing_service._filter_unsent_users(sample_users)
        
        assert len(unsent) == 40
        assert all(user.id not in [1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009] 
                   for user in unsent)
    
    @pytest.mark.asyncio
    async def test_filter_unsent_users_all_sent(self, mailing_service, sample_users):
        """Test filtering when all users have been sent messages."""
        mailing_service.progress_tracker.load_progress("https://t.me/testgroup")
        
        # Mark all users as sent
        for user in sample_users:
            mailing_service.progress_tracker.mark_sent(user.id)
        
        unsent = mailing_service._filter_unsent_users(sample_users)
        
        assert len(unsent) == 0


class TestMessageSending:
    """Tests for message sending functionality."""
    
    @pytest.mark.asyncio
    async def test_send_to_user_success(self, mailing_service, mock_telegram_service):
        """Test successful message send."""
        user = User(id=123, username="test", first_name="Test", last_name="User")
        message = "Hello!"
        
        # Mock successful send
        mock_telegram_service.send_message.return_value = SendResult(
            success=True,
            user_id=123
        )
        
        mailing_service.progress_tracker.load_progress("https://t.me/testgroup")
        
        result = await mailing_service._send_to_user(user, message)
        
        assert result.success
        assert mailing_service.progress_tracker.is_sent(123)
        assert mailing_service._messages_sent == 1
        assert mailing_service._messages_failed == 0
    
    @pytest.mark.asyncio
    async def test_send_to_user_failure(self, mailing_service, mock_telegram_service):
        """Test failed message send."""
        user = User(id=123, username="test", first_name="Test", last_name="User")
        message = "Hello!"
        
        # Mock failed send
        mock_telegram_service.send_message.return_value = SendResult(
            success=False,
            user_id=123,
            error="Network error"
        )
        
        mailing_service.progress_tracker.load_progress("https://t.me/testgroup")
        
        result = await mailing_service._send_to_user(user, message)
        
        assert not result.success
        assert not mailing_service.progress_tracker.is_sent(123)
        assert mailing_service._messages_sent == 0
        assert mailing_service._messages_failed == 1
    
    @pytest.mark.asyncio
    async def test_send_to_user_with_callback(self, mailing_service, mock_telegram_service):
        """Test message send with progress callback."""
        user = User(id=123, username="test", first_name="Test", last_name="User")
        message = "Hello!"
        callback = Mock()
        
        # Mock successful send
        mock_telegram_service.send_message.return_value = SendResult(
            success=True,
            user_id=123
        )
        
        mailing_service.progress_tracker.load_progress("https://t.me/testgroup")
        
        await mailing_service._send_to_user(user, message, progress_callback=callback)
        
        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0] == user
        assert args[1].success


class TestFloodWaitHandling:
    """Tests for FloodWait error handling."""
    
    @pytest.mark.asyncio
    async def test_handle_flood_wait(self, mailing_service):
        """Test FloodWait handling adds extra delay."""
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await mailing_service._handle_flood_wait(100)
            
            # Should wait 100 + (5-10) seconds
            mock_sleep.assert_called_once()
            wait_time = mock_sleep.call_args[0][0]
            assert 105 <= wait_time <= 110
    
    @pytest.mark.asyncio
    async def test_send_batch_with_flood_wait_retry(self, mailing_service, mock_telegram_service):
        """Test that FloodWait causes retry."""
        users = [User(id=123, username="test", first_name="Test", last_name="User")]
        message = "Hello!"
        
        # First call returns FloodWait, second call succeeds
        mock_telegram_service.send_message.side_effect = [
            SendResult(success=False, user_id=123, error="FloodWait", retry_after=1),
            SendResult(success=True, user_id=123)
        ]
        
        mailing_service.progress_tracker.load_progress("https://t.me/testgroup")
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            await mailing_service._send_batch(users, message, 1)
        
        # Should have called send_message twice (original + retry)
        assert mock_telegram_service.send_message.call_count == 2


class TestPowerManagement:
    """Tests for power management integration."""
    
    @pytest.mark.asyncio
    async def test_power_management_activated_during_mailing(
        self, mailing_service, mock_telegram_service, mock_power_manager, sample_users
    ):
        """Test that power management is activated during mailing."""
        # Mock successful sends
        mock_telegram_service.send_message.return_value = SendResult(
            success=True,
            user_id=1000
        )
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            await mailing_service.start_mailing(
                users=sample_users[:5],  # Small batch for quick test
                message="Test",
                group_url="https://t.me/testgroup"
            )
        
        # Power management should be activated and deactivated
        mock_power_manager.prevent_sleep.assert_called_once()
        mock_power_manager.allow_sleep.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_power_management_deactivated_on_error(
        self, mailing_service, mock_telegram_service, mock_power_manager, sample_users
    ):
        """Test that power management is deactivated even if error occurs."""
        # Mock send that raises exception
        mock_telegram_service.send_message.side_effect = Exception("Test error")
        
        with pytest.raises(Exception):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                await mailing_service.start_mailing(
                    users=sample_users[:5],
                    message="Test",
                    group_url="https://t.me/testgroup"
                )
        
        # Power management should still be deactivated
        mock_power_manager.allow_sleep.assert_called_once()


class TestResumeCapability:
    """Tests for resume capability after restart."""
    
    @pytest.mark.asyncio
    async def test_resume_skips_already_sent_users(
        self, mailing_service, mock_telegram_service, sample_users
    ):
        """Test that resuming skips users who already received messages."""
        # Mock successful sends
        mock_telegram_service.send_message.return_value = SendResult(
            success=True,
            user_id=1000
        )
        
        # First mailing: send to first 10 users
        mailing_service.progress_tracker.load_progress("https://t.me/testgroup")
        for i in range(10):
            mailing_service.progress_tracker.mark_sent(sample_users[i].id)
        
        # Resume mailing with all users
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await mailing_service.start_mailing(
                users=sample_users,
                message="Test",
                group_url="https://t.me/testgroup"
            )
        
        # Should have sent to 40 users (50 - 10 already sent)
        assert result["already_sent"] == 10
        assert result["messages_sent"] == 40
    
    @pytest.mark.asyncio
    async def test_resume_with_all_users_sent(
        self, mailing_service, mock_telegram_service, sample_users
    ):
        """Test resuming when all users already received messages."""
        # Mark all users as sent
        mailing_service.progress_tracker.load_progress("https://t.me/testgroup")
        for user in sample_users:
            mailing_service.progress_tracker.mark_sent(user.id)
        
        # Try to resume
        result = await mailing_service.start_mailing(
            users=sample_users,
            message="Test",
            group_url="https://t.me/testgroup"
        )
        
        # Should not send any messages
        assert result["already_sent"] == len(sample_users)
        assert result["messages_sent"] == 0
        assert result["batches_completed"] == 0


class TestDelayCalculation:
    """Tests for delay calculation integration."""
    
    @pytest.mark.asyncio
    async def test_delay_calculated_with_end_date(
        self, mailing_service, mock_telegram_service, sample_users
    ):
        """Test that delay is calculated when end_date is provided."""
        # Mock successful sends
        mock_telegram_service.send_message.return_value = SendResult(
            success=True,
            user_id=1000
        )
        
        end_date = datetime.now() + timedelta(days=7)
        
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await mailing_service.start_mailing(
                users=sample_users[:36],  # Exactly 2 batches
                message="Test",
                group_url="https://t.me/testgroup",
                end_date=end_date
            )
            
            # Should have waited between batches
            # Check that sleep was called with a reasonable delay
            sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
            # Filter out message delays (15-45 seconds)
            batch_delays = [delay for delay in sleep_calls if delay > 100]
            assert len(batch_delays) >= 1  # At least one batch delay
    
    @pytest.mark.asyncio
    async def test_delay_capped_at_24_hours(
        self, mailing_service, mock_telegram_service, sample_users
    ):
        """Test that delay is capped at 24 hours maximum."""
        # Mock successful sends
        mock_telegram_service.send_message.return_value = SendResult(
            success=True,
            user_id=1000
        )
        
        # Set end date very far in future to trigger cap
        end_date = datetime.now() + timedelta(days=365)
        
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await mailing_service.start_mailing(
                users=sample_users[:36],  # Exactly 2 batches
                message="Test",
                group_url="https://t.me/testgroup",
                end_date=end_date
            )
            
            # Check that no delay exceeds 24 hours (86400 seconds)
            sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert all(delay <= 86400 for delay in sleep_calls)


class TestValidation:
    """Tests for input validation."""
    
    @pytest.mark.asyncio
    async def test_start_mailing_empty_users_list(self, mailing_service):
        """Test that empty users list raises ValueError."""
        with pytest.raises(ValueError, match="Users list cannot be empty"):
            await mailing_service.start_mailing(
                users=[],
                message="Test",
                group_url="https://t.me/testgroup"
            )
    
    @pytest.mark.asyncio
    async def test_start_mailing_empty_message(self, mailing_service, sample_users):
        """Test that empty message raises ValueError."""
        with pytest.raises(ValueError, match="Message cannot be empty"):
            await mailing_service.start_mailing(
                users=sample_users,
                message="",
                group_url="https://t.me/testgroup"
            )
    
    @pytest.mark.asyncio
    async def test_start_mailing_already_running(
        self, mailing_service, mock_telegram_service, sample_users
    ):
        """Test that starting mailing while already running raises RuntimeError."""
        # Mock slow send to keep mailing running
        async def slow_send(*args, **kwargs):
            await asyncio.sleep(1)
            return SendResult(success=True, user_id=1000)
        
        mock_telegram_service.send_message.side_effect = slow_send
        
        # Start first mailing
        task = asyncio.create_task(
            mailing_service.start_mailing(
                users=sample_users,
                message="Test",
                group_url="https://t.me/testgroup"
            )
        )
        
        # Wait a bit for it to start
        await asyncio.sleep(0.1)
        
        # Try to start second mailing
        with pytest.raises(RuntimeError, match="already running"):
            await mailing_service.start_mailing(
                users=sample_users,
                message="Test",
                group_url="https://t.me/testgroup"
            )
        
        # Stop the first mailing
        mailing_service.stop_mailing()
        await task


class TestStopMailing:
    """Tests for stopping mailing gracefully."""
    
    @pytest.mark.asyncio
    async def test_stop_mailing_gracefully(
        self, mailing_service, mock_telegram_service, sample_users
    ):
        """Test that stop_mailing stops the process gracefully."""
        # Mock slow send
        async def slow_send(*args, **kwargs):
            await asyncio.sleep(0.1)
            return SendResult(success=True, user_id=1000)
        
        mock_telegram_service.send_message.side_effect = slow_send
        
        # Start mailing in background
        task = asyncio.create_task(
            mailing_service.start_mailing(
                users=sample_users,
                message="Test",
                group_url="https://t.me/testgroup"
            )
        )
        
        # Wait a bit then stop
        await asyncio.sleep(0.2)
        mailing_service.stop_mailing()
        
        # Wait for completion
        result = await task
        
        # Should have sent some but not all messages
        assert result["messages_sent"] < len(sample_users)
        assert result["messages_sent"] > 0


class TestStatistics:
    """Tests for statistics tracking."""
    
    @pytest.mark.asyncio
    async def test_get_statistics_during_mailing(
        self, mailing_service, mock_telegram_service, sample_users
    ):
        """Test getting statistics while mailing is in progress."""
        # Mock slow send
        async def slow_send(*args, **kwargs):
            await asyncio.sleep(0.1)
            return SendResult(success=True, user_id=1000)
        
        mock_telegram_service.send_message.side_effect = slow_send
        
        # Start mailing
        task = asyncio.create_task(
            mailing_service.start_mailing(
                users=sample_users[:5],
                message="Test",
                group_url="https://t.me/testgroup"
            )
        )
        
        # Wait a bit
        await asyncio.sleep(0.2)
        
        # Get statistics
        stats = mailing_service.get_statistics()
        
        assert stats["is_running"] is True
        assert stats["messages_sent"] >= 0
        
        # Stop and wait
        mailing_service.stop_mailing()
        await task
    
    def test_is_running_initially_false(self, mailing_service):
        """Test that is_running is False initially."""
        assert mailing_service.is_running() is False
    
    @pytest.mark.asyncio
    async def test_is_running_true_during_mailing(
        self, mailing_service, mock_telegram_service, sample_users
    ):
        """Test that is_running is True during mailing."""
        # Mock slow send
        async def slow_send(*args, **kwargs):
            await asyncio.sleep(0.1)
            return SendResult(success=True, user_id=1000)
        
        mock_telegram_service.send_message.side_effect = slow_send
        
        # Start mailing
        task = asyncio.create_task(
            mailing_service.start_mailing(
                users=sample_users[:5],
                message="Test",
                group_url="https://t.me/testgroup"
            )
        )
        
        # Wait a bit
        await asyncio.sleep(0.2)
        
        assert mailing_service.is_running() is True
        
        # Stop and wait
        mailing_service.stop_mailing()
        await task
        
        assert mailing_service.is_running() is False
