"""
Telegram Service for Telegram Mailer MacOS App.

Provides a wrapper around the Telethon client with:
- Connection management
- Authentication handling
- Group member retrieval
- Message sending with comprehensive error handling
- Automatic reconnection
- Session file management with secure permissions
"""

import asyncio
import random
import os
from pathlib import Path
from typing import List, Optional

from telethon import TelegramClient
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

from telegram.models import User, SendResult
from utils.constants import (
    SESSION_DIR,
    SESSION_FILE_PREFIX,
    MIN_MESSAGE_DELAY,
    MAX_MESSAGE_DELAY,
    MAX_RECONNECT_ATTEMPTS,
    RECONNECT_DELAY_SECONDS,
    FLOOD_WAIT_EXTRA_MIN,
    FLOOD_WAIT_EXTRA_MAX,
)


class TelegramService:
    """
    Service for interacting with Telegram API via Telethon.
    
    Handles all Telegram operations including authentication, group member
    retrieval, and message sending with comprehensive error handling.
    """
    
    def __init__(self, api_id: str, api_hash: str, session_dir: Path = SESSION_DIR):
        """
        Initialize Telegram service with API credentials.
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            session_dir: Directory for storing session files
            
        Note:
            Session file will be created at: session_dir/session_name.session
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_dir = session_dir
        
        # Ensure session directory exists
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create session file path
        session_path = self.session_dir / SESSION_FILE_PREFIX
        
        # Initialize Telethon client
        self.client = TelegramClient(
            str(session_path),
            api_id,
            api_hash
        )
        
        self.is_connected = False
        self.reconnect_attempts = 0
    
    async def connect(self) -> None:
        """
        Connect to Telegram.
        
        Raises:
            ConnectionError: If connection fails
        """
        try:
            await self.client.connect()
            self.is_connected = True
            
            # Set secure permissions on session file (600 - owner read/write only)
            session_file = self.session_dir / f"{SESSION_FILE_PREFIX}.session"
            if session_file.exists():
                os.chmod(session_file, 0o600)
                
        except Exception as e:
            self.is_connected = False
            raise ConnectionError(f"Failed to connect to Telegram: {e}") from e
    
    async def disconnect(self) -> None:
        """
        Disconnect from Telegram gracefully.
        
        Saves session and closes connection.
        """
        if self.is_connected:
            try:
                await self.client.disconnect()
            finally:
                self.is_connected = False
    
    async def is_authorized(self) -> bool:
        """
        Check if user is authorized.
        
        Returns:
            True if user is authorized, False otherwise
        """
        try:
            return await self.client.is_user_authorized()
        except Exception:
            return False
    
    async def send_code_request(self, phone: str) -> str:
        """
        Request authentication code from Telegram.
        
        Args:
            phone: Phone number in international format (e.g., +1234567890)
            
        Returns:
            Phone code hash for subsequent sign_in call
            
        Raises:
            PhoneNumberInvalidError: If phone number is invalid
            ConnectionError: If not connected to Telegram
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to Telegram. Call connect() first.")
        
        try:
            result = await self.client.send_code_request(phone)
            return result.phone_code_hash
        except PhoneNumberInvalidError as e:
            # Re-raise the original error to preserve Telethon's error message
            raise
    
    async def sign_in(
        self,
        phone: str,
        code: str,
        phone_code_hash: str,
        password: Optional[str] = None
    ) -> bool:
        """
        Sign in with authentication code and optional 2FA password.
        
        Args:
            phone: Phone number in international format
            code: Authentication code from SMS/Telegram
            phone_code_hash: Hash from send_code_request()
            password: 2FA password (optional, required if 2FA is enabled)
            
        Returns:
            True if authentication successful
            
        Raises:
            PhoneCodeInvalidError: If authentication code is invalid
            SessionPasswordNeededError: If 2FA is enabled but password not provided
            PasswordHashInvalidError: If 2FA password is invalid
            ConnectionError: If not connected to Telegram
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to Telegram. Call connect() first.")
        
        try:
            # Try to sign in with code
            await self.client.sign_in(phone, code, phone_code_hash=phone_code_hash)
            
            # Set secure permissions on session file after successful auth
            session_file = self.session_dir / f"{SESSION_FILE_PREFIX}.session"
            if session_file.exists():
                os.chmod(session_file, 0o600)
            
            return True
            
        except SessionPasswordNeededError:
            # 2FA is enabled, need password
            if password:
                try:
                    await self.client.sign_in(password=password)
                    
                    # Set secure permissions on session file
                    session_file = self.session_dir / f"{SESSION_FILE_PREFIX}.session"
                    if session_file.exists():
                        os.chmod(session_file, 0o600)
                    
                    return True
                except PasswordHashInvalidError:
                    # Re-raise the original error
                    raise
            else:
                # Re-raise the original error
                raise
    
    async def get_group_members(self, group_url: str) -> List[User]:
        """
        Get list of group members.
        
        Args:
            group_url: Group URL (e.g., https://t.me/groupname or @groupname)
            
        Returns:
            List of User objects representing group members
            
        Raises:
            ValueError: If group URL is invalid
            ChatAdminRequiredError: If user doesn't have access to the group
            InviteHashExpiredError: If invite link has expired
            ConnectionError: If not connected to Telegram
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to Telegram. Call connect() first.")
        
        try:
            # Get entity from URL
            entity = await self.client.get_entity(group_url)
            
            # Get participants
            participants = await self.client.get_participants(entity)
            
            # Convert to User model
            users = []
            for participant in participants:
                if isinstance(participant, TelethonUser):
                    user = User(
                        id=participant.id,
                        username=participant.username,
                        first_name=participant.first_name or "",
                        last_name=participant.last_name,
                        sent=False
                    )
                    users.append(user)
            
            return users
            
        except ValueError as e:
            raise ValueError(f"Invalid group URL: {group_url}") from e
        except ChatAdminRequiredError:
            # Re-raise the original error
            raise
        except InviteHashExpiredError:
            # Re-raise the original error
            raise
    
    async def send_message(
        self,
        user_id: int,
        message: str,
        delay_min: int = MIN_MESSAGE_DELAY,
        delay_max: int = MAX_MESSAGE_DELAY,
        link_preview: bool = True
    ) -> SendResult:
        """
        Send message to a user with random delay.
        
        Args:
            user_id: Telegram user ID
            message: Message text (can contain HTML formatting)
            delay_min: Minimum delay in seconds after sending (default: 15)
            delay_max: Maximum delay in seconds after sending (default: 45)
            
        Returns:
            SendResult with success status and error details if applicable
            
        Note:
            Automatically adds random delay after sending to mimic human behavior.
            Handles all Telegram errors gracefully and returns structured results.
        """
        if not self.is_connected:
            return SendResult(
                success=False,
                user_id=user_id,
                error="Not connected to Telegram"
            )
        
        try:
            # Send message with HTML parsing
            await self.client.send_message(
                user_id,
                message,
                parse_mode='html',
                link_preview=link_preview
            )
            
            # Random delay to mimic human behavior
            delay = random.randint(delay_min, delay_max)
            await asyncio.sleep(delay)
            
            return SendResult(
                success=True,
                user_id=user_id
            )
            
        except FloodWaitError as e:
            # Telegram requires waiting
            return SendResult(
                success=False,
                user_id=user_id,
                error=f"FloodWait: {e.seconds} seconds",
                retry_after=e.seconds
            )
            
        except UserPrivacyRestrictedError:
            # User privacy settings prevent message delivery
            # Mark as "success" to avoid retrying
            return SendResult(
                success=True,
                user_id=user_id,
                error="UserPrivacyRestricted"
            )
            
        except PeerFloodError:
            # Too many requests
            return SendResult(
                success=False,
                user_id=user_id,
                error="PeerFlood: Too many requests"
            )
            
        except ChatAdminRequiredError:
            # Admin rights required
            return SendResult(
                success=False,
                user_id=user_id,
                error="ChatAdminRequired: Admin rights needed"
            )
            
        except Exception as e:
            # Other errors
            return SendResult(
                success=False,
                user_id=user_id,
                error=f"Unexpected error: {str(e)}"
            )
    
    async def reconnect(self, max_attempts: int = MAX_RECONNECT_ATTEMPTS) -> bool:
        """
        Reconnect to Telegram after network errors.
        
        Args:
            max_attempts: Maximum number of reconnection attempts (default: 3)
            
        Returns:
            True if reconnection successful, False otherwise
            
        Note:
            Uses exponential backoff between attempts.
            Verifies authorization after reconnection.
        """
        for attempt in range(max_attempts):
            try:
                # Disconnect if still connected
                await self.disconnect()
                
                # Wait before reconnecting (exponential backoff)
                wait_time = RECONNECT_DELAY_SECONDS * (2 ** attempt)
                await asyncio.sleep(wait_time)
                
                # Try to reconnect
                await self.connect()
                
                # Verify authorization
                if await self.is_authorized():
                    self.reconnect_attempts = 0
                    return True
                else:
                    # Not authorized, can't continue
                    return False
                    
            except Exception as e:
                self.reconnect_attempts += 1
                
                # If this was the last attempt, give up
                if attempt == max_attempts - 1:
                    return False
                
                # Otherwise, continue to next attempt
                continue
        
        return False
