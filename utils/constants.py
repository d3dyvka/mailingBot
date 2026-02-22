"""
Constants and configuration paths for Telegram Mailer MacOS App.
"""

from pathlib import Path
import os

# Application data directory (MacOS standard location)
APP_NAME = "TelegramMailer"
APP_SUPPORT_DIR = Path.home() / "Library" / "Application Support" / APP_NAME

# Subdirectories
CONFIG_DIR = APP_SUPPORT_DIR
SESSION_DIR = APP_SUPPORT_DIR
PROGRESS_DIR = APP_SUPPORT_DIR
LOG_DIR = APP_SUPPORT_DIR

# File names
CONFIG_FILE = "config.json"
SESSION_FILE_PREFIX = "session_name"
PROGRESS_FILE_PREFIX = "progress"
ERROR_LOG_FILE = "errors.txt"

# Batch settings
DEFAULT_BATCH_SIZE = 18
MIN_SAFE_DELAY_HOURS = 20
MAX_DELAY_HOURS = 24

# Message delay settings (in seconds)
MIN_MESSAGE_DELAY = 15
MAX_MESSAGE_DELAY = 45

# Reconnection settings
MAX_RECONNECT_ATTEMPTS = 3
RECONNECT_DELAY_SECONDS = 5

# FloodWait additional delay (in seconds)
FLOOD_WAIT_EXTRA_MIN = 5
FLOOD_WAIT_EXTRA_MAX = 10


def ensure_app_directories():
    """
    Ensure all required application directories exist.
    Creates them if they don't exist.
    """
    directories = [
        APP_SUPPORT_DIR,
        CONFIG_DIR,
        SESSION_DIR,
        PROGRESS_DIR,
        LOG_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        
    return APP_SUPPORT_DIR
