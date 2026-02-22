"""
Unit tests for TelegramService.

Tests Telegram API interactions including:
- Connection management
- Authentication
- Group member retrieval
- Message sending with error handling
- Automatic reconnection
- Session file permissions
"""

import pytest
import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, MagicMock

from telethon.errors import (
    FloodWaitError,
    UserPrivacyRestrictedError,
    PeerFloodError,
    ChatAdminRequiredError,
    PhoneNumberInvalidError,
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
    PasswordHashInvalidError,
    InviteHashExpiredError,
)
from telethon.tl.types import User as TelethonUser

from telegram.telegram_service import TelegramService
from telegram.models import User, SendResult


@pytest.fixture
def temp_session_dir():
    """Create a temporary directory for session files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_telegram_client():
    """Create a mock TelegramClient."""
    with patch('telegram.telegram_service.TelegramClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def telegram_service(temp_session_dir, mock_telegram_client):
    """Create a TelegramService instance with mocked client."""
    service = TelegramService(
        api_id="123456",
        api_hash="abcdef123456",
        session_dir=temp_session_dir
    )
    return service


class TestTelegramServiceInit:
    """Test TelegramService initialization."""
    
    def test_init_creates_session_directory(self, temp_session_dir, mock_telegram_client):
        """Test that initialization creates session directory."""
        session_dir = temp_session_dir / "new_dir"
        assert not session_dir.exists()
        
        service = TelegramService("123456", "abcdef", session_dir)
        
        assert session_dir.exists()
        assert service.session_dir == session_dir
    
    def test_init_sets_attributes(self, telegram_service):
        """Test that initialization sets correct attributes."""
        assert telegram_service.api_id == "123456"
        assert telegram_service.api_hash == "abcdef123456"
        assert telegram_service.is_connected == False
        assert telegram_service.reconnect_attempts == 0


class TestConnection:
    """Test connection management."""
    
    @pytest.mark.asyncio
    async def test_connect_success(self, telegram_service, mock_telegram_client):
        """Test successful connection."""
        mock_telegram_client.connect = AsyncMock()
        
        await telegram_service.connect()
        
        assert telegram_service.is_connected == True
        mock_telegram_client.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_sets_session_file_permissions(self, telegram_service, temp_session_dir, mock_telegram_client):
        """Test that connect sets session file permissions to 600."""
        mock_telegram_client.connect = AsyncMock()
        
        # Create a dummy session file
        session_file = temp_session_dir / "session_name.session"
        session_file.touch()
        
        await telegram_service.connect()
        
        # Check permissions (600 = owner read/write only)
        file_stat = os.stat(session_file)
        file_permissions = oct(file_stat.st_mode)[-3:]
        assert file_permissions == "600"
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, telegram_service, mock_telegram_client):
        """Test connection failure."""
        mock_telegram_client.connect = AsyncMock(side_effect=Exception("Connection failed"))
        
        with pytest.raises(ConnectionError, match="Failed to connect"):
            await telegram_service.connect()
        
        assert telegram_service.is_connected == False
    
    @pytest.mark.asyncio
    async def test_disconnect(self, telegram_service, mock_telegram_client):
        """Test disconnection."""
        mock_telegram_client.disconnect = AsyncMock()
        telegram_service.is_connected = True
        
        await telegram_service.disconnect()
        
        assert telegram_service.is_connected == False
        mock_telegram_client.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self, telegram_service, mock_telegram_client):
        """Test disconnect when not connected doesn't call client."""
        mock_telegram_client.disconnect = AsyncMock()
        telegram_service.is_connected = False
        
        await telegram_service.disconnect()
        
        mock_telegram_client.disconnect.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_is_authorized_true(self, telegram_service, mock_telegram_client):
        """Test is_authorized returns True when authorized."""
        mock_telegram_client.is_user_authorized = AsyncMock(return_value=True)
        
        result = await telegram_service.is_authorized()
        
        assert result == True
    
    @pytest.mark.asyncio
    async def test_is_authorized_false(self, telegram_service, mock_telegram_client):
        """Test is_authorized returns False when not authorized."""
        mock_telegram_client.is_user_authorized = AsyncMock(return_value=False)
        
        result = await telegram_service.is_authorized()
        
        assert result == False
    
    @pytest.mark.asyncio
    async def test_is_authorized_handles_exception(self, telegram_service, mock_telegram_client):
        """Test is_authorized returns False on exception."""
        mock_telegram_client.is_user_authorized = AsyncMock(side_effect=Exception("Error"))
        
        result = await telegram_service.is_authorized()
        
        assert result == False


class TestAuthentication:
    """Test authentication methods."""
    
    @pytest.mark.asyncio
    async def test_send_code_request_success(self, telegram_service, mock_telegram_client):
        """Test successful code request."""
        telegram_service.is_connected = True
        mock_result = Mock()
        mock_result.phone_code_hash = "test_hash_123"
        mock_telegram_client.send_code_request = AsyncMock(return_value=mock_result)
        
        phone_code_hash = await telegram_service.send_code_request("+1234567890")
        
        assert phone_code_hash == "test_hash_123"
        mock_telegram_client.send_code_request.assert_called_once_with("+1234567890")
    
    @pytest.mark.asyncio
    async def test_send_code_request_not_connected(self, telegram_service):
        """Test code request fails when not connected."""
        telegram_service.is_connected = False
        
        with pytest.raises(ConnectionError, match="Not connected"):
            await telegram_service.send_code_request("+1234567890")
    
    @pytest.mark.asyncio
    async def test_send_code_request_invalid_phone(self, telegram_service, mock_telegram_client):
        """Test code request with invalid phone number."""
        telegram_service.is_connected = True
        mock_telegram_client.send_code_request = AsyncMock(
            side_effect=PhoneNumberInvalidError("Invalid phone")
        )
        
        with pytest.raises(PhoneNumberInvalidError):
            await telegram_service.send_code_request("invalid")
    
    @pytest.mark.asyncio
    async def test_sign_in_success(self, telegram_service, mock_telegram_client, temp_session_dir):
        """Test successful sign in."""
        telegram_service.is_connected = True
        mock_telegram_client.sign_in = AsyncMock()
        
        # Create session file to test permissions
        session_file = temp_session_dir / "session_name.session"
        session_file.touch()
        
        result = await telegram_service.sign_in("+1234567890", "12345", "hash123")
        
        assert result == True
        mock_telegram_client.sign_in.assert_called_once_with(
            "+1234567890", "12345", phone_code_hash="hash123"
        )
        
        # Check session file permissions
        file_stat = os.stat(session_file)
        file_permissions = oct(file_stat.st_mode)[-3:]
        assert file_permissions == "600"
    
    @pytest.mark.asyncio
    async def test_sign_in_not_connected(self, telegram_service):
        """Test sign in fails when not connected."""
        telegram_service.is_connected = False
        
        with pytest.raises(ConnectionError, match="Not connected"):
            await telegram_service.sign_in("+1234567890", "12345", "hash123")
    
    @pytest.mark.asyncio
    async def test_sign_in_invalid_code(self, telegram_service, mock_telegram_client):
        """Test sign in with invalid code."""
        telegram_service.is_connected = True
        mock_telegram_client.sign_in = AsyncMock(
            side_effect=PhoneCodeInvalidError("Invalid code")
        )
        
        with pytest.raises(PhoneCodeInvalidError):
            await telegram_service.sign_in("+1234567890", "wrong", "hash123")
    
    @pytest.mark.asyncio
    async def test_sign_in_2fa_required_no_password(self, telegram_service, mock_telegram_client):
        """Test sign in when 2FA required but no password provided."""
        telegram_service.is_connected = True
        mock_telegram_client.sign_in = AsyncMock(
            side_effect=SessionPasswordNeededError("2FA required")
        )
        
        with pytest.raises(SessionPasswordNeededError):
            await telegram_service.sign_in("+1234567890", "12345", "hash123")
    
    @pytest.mark.asyncio
    async def test_sign_in_2fa_success(self, telegram_service, mock_telegram_client, temp_session_dir):
        """Test successful sign in with 2FA."""
        telegram_service.is_connected = True
        
        # First call raises SessionPasswordNeededError, second succeeds
        mock_telegram_client.sign_in = AsyncMock(
            side_effect=[SessionPasswordNeededError("2FA"), None]
        )
        
        # Create session file
        session_file = temp_session_dir / "session_name.session"
        session_file.touch()
        
        result = await telegram_service.sign_in(
            "+1234567890", "12345", "hash123", password="my2fapass"
        )
        
        assert result == True
        assert mock_telegram_client.sign_in.call_count == 2
        
        # Check second call was with password
        second_call = mock_telegram_client.sign_in.call_args_list[1]
        assert second_call[1] == {'password': 'my2fapass'}
    
    @pytest.mark.asyncio
    async def test_sign_in_2fa_invalid_password(self, telegram_service, mock_telegram_client):
        """Test sign in with invalid 2FA password."""
        telegram_service.is_connected = True
        
        # First call raises SessionPasswordNeededError, second raises PasswordHashInvalidError
        mock_telegram_client.sign_in = AsyncMock(
            side_effect=[
                SessionPasswordNeededError("2FA"),
                PasswordHashInvalidError("Wrong password")
            ]
        )
        
        with pytest.raises(PasswordHashInvalidError):
            await telegram_service.sign_in(
                "+1234567890", "12345", "hash123", password="wrongpass"
            )


class TestGroupMembers:
    """Test group member retrieval."""
    
    @pytest.mark.asyncio
    async def test_get_group_members_success(self, telegram_service, mock_telegram_client):
        """Test successful group member retrieval."""
        telegram_service.is_connected = True
        
        # Mock participants
        mock_user1 = TelethonUser(
            id=123,
            first_name="John",
            last_name="Doe",
            username="johndoe",
            is_self=False,
            contact=False,
            mutual_contact=False,
            deleted=False,
            bot=False,
            bot_chat_history=False,
            bot_nochats=False,
            verified=False,
            restricted=False,
            min=False,
            bot_inline_geo=False,
            support=False,
            scam=False,
            apply_min_photo=False,
            fake=False,
            bot_attach_menu=False,
            premium=False,
            attach_menu_enabled=False,
            bot_can_edit=False,
            close_friend=False,
            stories_hidden=False,
            stories_unavailable=False,
            access_hash=0,
            phone=None,
            photo=None,
            status=None,
            bot_info_version=None,
            restriction_reason=None,
            bot_inline_placeholder=None,
            lang_code=None,
            emoji_status=None,
            usernames=None,
            stories_max_id=None,
            color=None,
            profile_color=None
        )
        
        mock_user2 = TelethonUser(
            id=456,
            first_name="Jane",
            last_name=None,
            username=None,
            is_self=False,
            contact=False,
            mutual_contact=False,
            deleted=False,
            bot=False,
            bot_chat_history=False,
            bot_nochats=False,
            verified=False,
            restricted=False,
            min=False,
            bot_inline_geo=False,
            support=False,
            scam=False,
            apply_min_photo=False,
            fake=False,
            bot_attach_menu=False,
            premium=False,
            attach_menu_enabled=False,
            bot_can_edit=False,
            close_friend=False,
            stories_hidden=False,
            stories_unavailable=False,
            access_hash=0,
            phone=None,
            photo=None,
            status=None,
            bot_info_version=None,
            restriction_reason=None,
            bot_inline_placeholder=None,
            lang_code=None,
            emoji_status=None,
            usernames=None,
            stories_max_id=None,
            color=None,
            profile_color=None
        )
        
        mock_telegram_client.get_entity = AsyncMock(return_value=Mock())
        mock_telegram_client.get_participants = AsyncMock(return_value=[mock_user1, mock_user2])
        
        users = await telegram_service.get_group_members("https://t.me/testgroup")
        
        assert len(users) == 2
        assert users[0].id == 123
        assert users[0].first_name == "John"
        assert users[0].last_name == "Doe"
        assert users[0].username == "johndoe"
        assert users[0].sent == False
        
        assert users[1].id == 456
        assert users[1].first_name == "Jane"
        assert users[1].last_name is None
        assert users[1].username is None
    
    @pytest.mark.asyncio
    async def test_get_group_members_not_connected(self, telegram_service):
        """Test group member retrieval fails when not connected."""
        telegram_service.is_connected = False
        
        with pytest.raises(ConnectionError, match="Not connected"):
            await telegram_service.get_group_members("https://t.me/testgroup")
    
    @pytest.mark.asyncio
    async def test_get_group_members_invalid_url(self, telegram_service, mock_telegram_client):
        """Test group member retrieval with invalid URL."""
        telegram_service.is_connected = True
        mock_telegram_client.get_entity = AsyncMock(side_effect=ValueError("Invalid URL"))
        
        with pytest.raises(ValueError, match="Invalid group URL"):
            await telegram_service.get_group_members("invalid_url")
    
    @pytest.mark.asyncio
    async def test_get_group_members_admin_required(self, telegram_service, mock_telegram_client):
        """Test group member retrieval when admin rights required."""
        telegram_service.is_connected = True
        mock_telegram_client.get_entity = AsyncMock(return_value=Mock())
        mock_telegram_client.get_participants = AsyncMock(
            side_effect=ChatAdminRequiredError("Admin required")
        )
        
        with pytest.raises(ChatAdminRequiredError):
            await telegram_service.get_group_members("https://t.me/testgroup")
    
    @pytest.mark.asyncio
    async def test_get_group_members_invite_expired(self, telegram_service, mock_telegram_client):
        """Test group member retrieval with expired invite."""
        telegram_service.is_connected = True
        mock_telegram_client.get_entity = AsyncMock(
            side_effect=InviteHashExpiredError("Invite expired")
        )
        
        with pytest.raises(InviteHashExpiredError):
            await telegram_service.get_group_members("https://t.me/+abc123")


class TestMessageSending:
    """Test message sending with error handling."""
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, telegram_service, mock_telegram_client):
        """Test successful message sending."""
        telegram_service.is_connected = True
        mock_telegram_client.send_message = AsyncMock()
        
        # Mock sleep to speed up test
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await telegram_service.send_message(123, "Hello!")
        
        assert result.success == True
        assert result.user_id == 123
        assert result.error is None
        mock_telegram_client.send_message.assert_called_once_with(
            123, "Hello!", parse_mode='html'
        )
    
    @pytest.mark.asyncio
    async def test_send_message_not_connected(self, telegram_service):
        """Test message sending when not connected."""
        telegram_service.is_connected = False
        
        result = await telegram_service.send_message(123, "Hello!")
        
        assert result.success == False
        assert result.user_id == 123
        assert "Not connected" in result.error
    
    @pytest.mark.asyncio
    async def test_send_message_flood_wait_error(self, telegram_service, mock_telegram_client):
        """Test message sending with FloodWaitError."""
        telegram_service.is_connected = True
        
        # Create FloodWaitError - it stores seconds as an attribute
        flood_error = FloodWaitError("Flood wait")
        flood_error.seconds = 3600
        mock_telegram_client.send_message = AsyncMock(side_effect=flood_error)
        
        result = await telegram_service.send_message(123, "Hello!")
        
        assert result.success == False
        assert result.user_id == 123
        assert "FloodWait" in result.error
        assert result.retry_after == 3600
    
    @pytest.mark.asyncio
    async def test_send_message_user_privacy_error(self, telegram_service, mock_telegram_client):
        """Test message sending with UserPrivacyRestrictedError."""
        telegram_service.is_connected = True
        mock_telegram_client.send_message = AsyncMock(
            side_effect=UserPrivacyRestrictedError("Privacy restricted")
        )
        
        result = await telegram_service.send_message(123, "Hello!")
        
        # UserPrivacyRestrictedError is marked as "success" to avoid retrying
        assert result.success == True
        assert result.user_id == 123
        assert result.error == "UserPrivacyRestricted"
    
    @pytest.mark.asyncio
    async def test_send_message_peer_flood_error(self, telegram_service, mock_telegram_client):
        """Test message sending with PeerFloodError."""
        telegram_service.is_connected = True
        mock_telegram_client.send_message = AsyncMock(
            side_effect=PeerFloodError("Too many requests")
        )
        
        result = await telegram_service.send_message(123, "Hello!")
        
        assert result.success == False
        assert result.user_id == 123
        assert "PeerFlood" in result.error
    
    @pytest.mark.asyncio
    async def test_send_message_chat_admin_required_error(self, telegram_service, mock_telegram_client):
        """Test message sending with ChatAdminRequiredError."""
        telegram_service.is_connected = True
        mock_telegram_client.send_message = AsyncMock(
            side_effect=ChatAdminRequiredError("Admin required")
        )
        
        result = await telegram_service.send_message(123, "Hello!")
        
        assert result.success == False
        assert result.user_id == 123
        assert "ChatAdminRequired" in result.error
    
    @pytest.mark.asyncio
    async def test_send_message_unexpected_error(self, telegram_service, mock_telegram_client):
        """Test message sending with unexpected error."""
        telegram_service.is_connected = True
        mock_telegram_client.send_message = AsyncMock(
            side_effect=Exception("Unexpected error")
        )
        
        result = await telegram_service.send_message(123, "Hello!")
        
        assert result.success == False
        assert result.user_id == 123
        assert "Unexpected error" in result.error
    
    @pytest.mark.asyncio
    async def test_send_message_with_html_formatting(self, telegram_service, mock_telegram_client):
        """Test message sending with HTML formatting."""
        telegram_service.is_connected = True
        mock_telegram_client.send_message = AsyncMock()
        
        message = "<b>Bold</b> and <i>italic</i> text"
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await telegram_service.send_message(123, message)
        
        assert result.success == True
        mock_telegram_client.send_message.assert_called_once_with(
            123, message, parse_mode='html'
        )


class TestReconnection:
    """Test automatic reconnection."""
    
    @pytest.mark.asyncio
    async def test_reconnect_success_first_attempt(self, telegram_service, mock_telegram_client):
        """Test successful reconnection on first attempt."""
        telegram_service.is_connected = True
        mock_telegram_client.disconnect = AsyncMock()
        mock_telegram_client.connect = AsyncMock()
        mock_telegram_client.is_user_authorized = AsyncMock(return_value=True)
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await telegram_service.reconnect(max_attempts=3)
        
        assert result == True
        assert telegram_service.reconnect_attempts == 0
        mock_telegram_client.disconnect.assert_called_once()
        mock_telegram_client.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reconnect_success_after_retries(self, telegram_service, mock_telegram_client):
        """Test successful reconnection after retries."""
        telegram_service.is_connected = True
        mock_telegram_client.disconnect = AsyncMock()
        
        # Fail first two attempts, succeed on third
        mock_telegram_client.connect = AsyncMock(
            side_effect=[Exception("Failed"), Exception("Failed"), None]
        )
        mock_telegram_client.is_user_authorized = AsyncMock(return_value=True)
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await telegram_service.reconnect(max_attempts=3)
        
        assert result == True
        assert telegram_service.reconnect_attempts == 0
        assert mock_telegram_client.connect.call_count == 3
    
    @pytest.mark.asyncio
    async def test_reconnect_failure_all_attempts(self, telegram_service, mock_telegram_client):
        """Test reconnection failure after all attempts."""
        telegram_service.is_connected = True
        mock_telegram_client.disconnect = AsyncMock()
        mock_telegram_client.connect = AsyncMock(side_effect=Exception("Failed"))
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await telegram_service.reconnect(max_attempts=3)
        
        assert result == False
        assert telegram_service.reconnect_attempts == 3
        assert mock_telegram_client.connect.call_count == 3
    
    @pytest.mark.asyncio
    async def test_reconnect_not_authorized_after_reconnect(self, telegram_service, mock_telegram_client):
        """Test reconnection fails if not authorized after reconnect."""
        telegram_service.is_connected = True
        mock_telegram_client.disconnect = AsyncMock()
        mock_telegram_client.connect = AsyncMock()
        mock_telegram_client.is_user_authorized = AsyncMock(return_value=False)
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await telegram_service.reconnect(max_attempts=3)
        
        assert result == False
    
    @pytest.mark.asyncio
    async def test_reconnect_exponential_backoff(self, telegram_service, mock_telegram_client):
        """Test that reconnection uses exponential backoff."""
        telegram_service.is_connected = True
        mock_telegram_client.disconnect = AsyncMock()
        mock_telegram_client.connect = AsyncMock(
            side_effect=[Exception("Failed"), Exception("Failed"), None]
        )
        mock_telegram_client.is_user_authorized = AsyncMock(return_value=True)
        
        sleep_times = []
        
        async def mock_sleep(seconds):
            sleep_times.append(seconds)
        
        with patch('asyncio.sleep', side_effect=mock_sleep):
            await telegram_service.reconnect(max_attempts=3)
        
        # Check exponential backoff: 5, 10, 20 seconds
        assert len(sleep_times) == 3
        assert sleep_times[0] == 5  # 5 * 2^0
        assert sleep_times[1] == 10  # 5 * 2^1
        assert sleep_times[2] == 20  # 5 * 2^2
