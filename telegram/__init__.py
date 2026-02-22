"""
Telegram integration module for Telegram Mailer MacOS App.

This module handles all Telegram API interactions, including:
- Authentication and session management
- Group member retrieval
- Message sending with error handling
- Automatic reconnection
"""

from telegram.telegram_service import TelegramService
from telegram.models import User, SendResult

__all__ = ['TelegramService', 'User', 'SendResult']
