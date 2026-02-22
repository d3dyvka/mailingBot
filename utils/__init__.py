"""
Utility module for Telegram Mailer MacOS App.

This module contains utility classes and functions, including:
- Progress tracking
- Delay calculation
- Error logging
- Power management
"""

# Imports will be added as modules are implemented
from .progress_tracker import ProgressTracker
from .delay_calculator import DelayCalculator, DelayResult
from .error_logger import ErrorLogger
from .power_manager import PowerManager

__all__ = ['ProgressTracker', 'DelayCalculator', 'DelayResult', 'ErrorLogger', 'PowerManager']
