"""
Configuration management module for Telegram Mailer MacOS App.

This module handles application configuration, including:
- API credentials management
- Configuration persistence
- Secure storage via MacOS Keychain
"""

from .config_manager import ConfigManager

__all__ = ['ConfigManager']
