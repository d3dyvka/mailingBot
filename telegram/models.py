"""
Data models for Telegram Mailer MacOS App.

Defines data structures used throughout the application for
representing users, send results, and other Telegram-related data.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """
    Represents a Telegram user from a group.
    
    Attributes:
        id: Telegram user ID
        username: Telegram username (optional)
        first_name: User's first name
        last_name: User's last name (optional)
        sent: Whether a message has been sent to this user
    """
    id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    sent: bool = False
    
    def __str__(self) -> str:
        """String representation of the user."""
        name_parts = [self.first_name]
        if self.last_name:
            name_parts.append(self.last_name)
        name = " ".join(name_parts)
        
        if self.username:
            return f"{name} (@{self.username})"
        return name


@dataclass
class SendResult:
    """
    Result of a message send operation.
    
    Attributes:
        success: Whether the message was sent successfully
        user_id: ID of the target user
        error: Error message if send failed (optional)
        retry_after: Seconds to wait before retry for FloodWait errors (optional)
    """
    success: bool
    user_id: int
    error: Optional[str] = None
    retry_after: Optional[int] = None
    
    def __str__(self) -> str:
        """String representation of the send result."""
        if self.success:
            if self.error:
                return f"User {self.user_id}: Skipped ({self.error})"
            return f"User {self.user_id}: Success"
        else:
            if self.retry_after:
                return f"User {self.user_id}: Failed - {self.error} (retry after {self.retry_after}s)"
            return f"User {self.user_id}: Failed - {self.error}"
