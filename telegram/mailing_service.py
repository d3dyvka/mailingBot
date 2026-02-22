"""
Mailing Service for Telegram Mailer MacOS App.

Coordinates the entire mailing process with:
- Batch processing (18 users per batch)
- Random delays between messages (15-45 seconds)
- Calculated delays between batches (max 24 hours)
- Progress tracking and persistence
- Error logging
- Power management (prevent sleep)
- FloodWait handling
- Resume capability (skip already processed users)
"""

import asyncio
import random
from typing import List, Optional, Callable
from datetime import datetime, timedelta

from telegram.telegram_service import TelegramService
from telegram.models import User, SendResult
from utils.progress_tracker import ProgressTracker
from utils.delay_calculator import DelayCalculator, DelayResult
from utils.error_logger import ErrorLogger
from utils.power_manager import PowerManager
from utils.constants import (
    DEFAULT_BATCH_SIZE,
    MIN_MESSAGE_DELAY,
    MAX_MESSAGE_DELAY,
    FLOOD_WAIT_EXTRA_MIN,
    FLOOD_WAIT_EXTRA_MAX,
    MAX_DELAY_HOURS,
)


class MailingService:
    """
    Coordinates the mailing campaign process.
    
    Manages the entire lifecycle of a mailing campaign including:
    - Splitting users into batches
    - Sending messages with appropriate delays
    - Tracking progress and handling errors
    - Preventing system sleep during operation
    - Resuming from interruptions
    
    Attributes:
        telegram_service: Service for Telegram API operations
        progress_tracker: Tracks which users have received messages
        delay_calculator: Calculates optimal delays between batches
        error_logger: Logs all errors automatically
        power_manager: Prevents system sleep during mailing
        batch_size: Number of users per batch (default: 18)
    """
    
    def __init__(
        self,
        telegram_service: TelegramService,
        progress_tracker: ProgressTracker,
        delay_calculator: DelayCalculator,
        error_logger: ErrorLogger,
        power_manager: PowerManager,
        batch_size: int = DEFAULT_BATCH_SIZE
    ):
        """
        Initialize the mailing service.
        
        Args:
            telegram_service: Telegram API service
            progress_tracker: Progress tracking service
            delay_calculator: Delay calculation service
            error_logger: Error logging service
            power_manager: Power management service
            batch_size: Number of users per batch (default: 18)
        """
        self.telegram_service = telegram_service
        self.progress_tracker = progress_tracker
        self.delay_calculator = delay_calculator
        self.error_logger = error_logger
        self.power_manager = power_manager
        self.batch_size = batch_size
        
        # State tracking
        self._is_running = False
        self._should_stop = False
        self._current_batch = 0
        self._messages_sent = 0
        self._messages_failed = 0
    
    def _split_into_batches(self, users: List[User]) -> List[List[User]]:
        """
        Split users into batches of specified size.
        
        Args:
            users: List of users to split
            
        Returns:
            List of batches, where each batch is a list of users
            
        Note:
            All batches will have exactly batch_size users except possibly
            the last batch which may have fewer.
        """
        batches = []
        for i in range(0, len(users), self.batch_size):
            batch = users[i:i + self.batch_size]
            batches.append(batch)
        return batches
    
    def _filter_unsent_users(self, users: List[User]) -> List[User]:
        """
        Filter out users who have already received messages.
        
        Args:
            users: List of all users
            
        Returns:
            List of users who haven't received messages yet
        """
        unsent_users = []
        for user in users:
            if not self.progress_tracker.is_sent(user.id):
                unsent_users.append(user)
        return unsent_users
    
    async def _send_to_user(
        self,
        user: User,
        message: str,
        progress_callback: Optional[Callable] = None,
        link_preview: bool = True
    ) -> SendResult:
        """
        Send message to a single user with error handling.
        
        Args:
            user: User to send message to
            message: Message text (HTML formatted)
            progress_callback: Optional callback for progress updates
            
        Returns:
            SendResult with success status and error details
        """
        # Send message
        result = await self.telegram_service.send_message(
            user.id,
            message,
            delay_min=MIN_MESSAGE_DELAY,
            delay_max=MAX_MESSAGE_DELAY,
            link_preview=link_preview
        )
        
        # Handle result
        if result.success:
            # Mark as sent in progress tracker
            self.progress_tracker.mark_sent(user.id)
            self._messages_sent += 1
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(user, result)
        else:
            # Log error
            self._messages_failed += 1
            
            context = {
                "user_id": user.id,
                "username": user.username,
                "batch": self._current_batch,
                "error": result.error
            }
            
            self.error_logger.log_error(
                error_type="MessageSendError",
                message=f"Failed to send message to user {user.id}",
                context=context
            )
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(user, result)
        
        return result
    
    async def _handle_flood_wait(self, seconds: int) -> None:
        """
        Handle FloodWait error by waiting the specified time plus extra.
        
        Args:
            seconds: Number of seconds Telegram requires us to wait
        """
        # Add random extra delay (5-10 seconds)
        extra_delay = random.randint(FLOOD_WAIT_EXTRA_MIN, FLOOD_WAIT_EXTRA_MAX)
        total_wait = seconds + extra_delay
        
        # Log the wait
        self.error_logger.log_error(
            error_type="FloodWait",
            message=f"Waiting {total_wait} seconds (required: {seconds}s + extra: {extra_delay}s)",
            context={"batch": self._current_batch}
        )
        
        # Wait
        await asyncio.sleep(total_wait)
    
    async def _send_batch(
        self,
        batch: List[User],
        message: str,
        batch_number: int,
        progress_callback: Optional[Callable] = None,
        link_preview: bool = True
    ) -> None:
        """
        Send messages to all users in a batch.
        
        Args:
            batch: List of users in this batch
            message: Message text to send
            batch_number: Batch number (for logging)
            progress_callback: Optional callback for progress updates
        """
        self._current_batch = batch_number
        
        for user in batch:
            # Check if we should stop
            if self._should_stop:
                break
            
            # Send message
            result = await self._send_to_user(user, message, progress_callback, link_preview)
            
            # Handle FloodWait
            if not result.success and result.retry_after:
                await self._handle_flood_wait(result.retry_after)
                
                # Retry sending to this user
                result = await self._send_to_user(user, message, progress_callback, link_preview)
    
    async def _wait_between_batches(
        self,
        delay_hours: float,
        batch_callback: Optional[Callable] = None
    ) -> None:
        """
        Wait between batches with optional progress callback.
        
        Args:
            delay_hours: Hours to wait
            batch_callback: Optional callback for batch completion updates
        """
        # Cap delay at maximum 24 hours
        if delay_hours > MAX_DELAY_HOURS:
            delay_hours = MAX_DELAY_HOURS
        
        delay_seconds = delay_hours * 3600
        
        # Call batch callback if provided
        if batch_callback:
            batch_callback(delay_seconds)
        
        # Wait
        await asyncio.sleep(delay_seconds)
    
    async def start_mailing(
        self,
        users: List[User],
        message: str,
        group_url: str,
        end_date: Optional[datetime] = None,
        progress_callback: Optional[Callable] = None,
        batch_callback: Optional[Callable] = None,
        link_preview: bool = True
    ) -> dict:
        """
        Start the mailing campaign.
        
        This is the main entry point for starting a mailing campaign. It:
        1. Loads previous progress (if any)
        2. Filters out already-processed users
        3. Splits remaining users into batches
        4. Calculates optimal delays between batches
        5. Activates power management (prevent sleep)
        6. Sends messages batch by batch with delays
        7. Handles errors and FloodWait automatically
        8. Saves progress after each message
        9. Deactivates power management when done
        
        Args:
            users: List of all users in the group
            message: Message text to send (HTML formatted)
            group_url: URL of the Telegram group
            end_date: Target completion date (optional, for delay calculation)
            progress_callback: Optional callback(user, result) for each message
            batch_callback: Optional callback(delay_seconds) for batch completion
            
        Returns:
            dict: Statistics with keys:
                - total_users: Total number of users
                - messages_sent: Number of messages successfully sent
                - messages_failed: Number of failed messages
                - batches_completed: Number of batches completed
                - already_sent: Number of users who already received messages
                
        Raises:
            ValueError: If users list is empty or message is empty
            RuntimeError: If mailing is already running
        """
        # Validation
        if not users:
            raise ValueError("Users list cannot be empty")
        
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")
        
        if self._is_running:
            raise RuntimeError("Mailing is already running")
        
        # Initialize state
        self._is_running = True
        self._should_stop = False
        self._current_batch = 0
        self._messages_sent = 0
        self._messages_failed = 0
        
        try:
            # Load progress
            self.progress_tracker.load_progress(group_url)
            self.progress_tracker.set_total_users(len(users))
            
            # Filter out already-sent users
            unsent_users = self._filter_unsent_users(users)
            already_sent_count = len(users) - len(unsent_users)
            
            if not unsent_users:
                # All users already received messages
                return {
                    "total_users": len(users),
                    "messages_sent": 0,
                    "messages_failed": 0,
                    "batches_completed": 0,
                    "already_sent": already_sent_count
                }
            
            # Split into batches
            batches = self._split_into_batches(unsent_users)
            
            # Calculate delay between batches
            delay_hours = 0
            if end_date and len(batches) > 1:
                delay_result = self.delay_calculator.calculate_delay(
                    total_users=len(unsent_users),
                    end_date=end_date,
                    start_date=datetime.now()
                )
                delay_hours = delay_result.delay_hours
                
                # Log delay calculation
                if delay_result.warning:
                    self.error_logger.log_error(
                        error_type="DelayWarning",
                        message=delay_result.warning,
                        context={
                            "delay_hours": delay_hours,
                            "num_batches": len(batches),
                            "is_safe": delay_result.is_safe
                        }
                    )
            
            # Activate power management
            self.power_manager.prevent_sleep()
            
            # Process batches
            batches_completed = 0
            for i, batch in enumerate(batches):
                # Check if we should stop
                if self._should_stop:
                    break
                
                # Send batch
                await self._send_batch(
                    batch=batch,
                    message=message,
                    batch_number=i + 1,
                    progress_callback=progress_callback,
                    link_preview=link_preview
                )
                
                batches_completed += 1
                
                # Wait between batches (except after last batch)
                if i < len(batches) - 1 and not self._should_stop:
                    await self._wait_between_batches(
                        delay_hours=delay_hours,
                        batch_callback=batch_callback
                    )
            
            # Update summary in progress file
            self.progress_tracker.update_summary(
                total_users=len(users),
                sent_count=self._messages_sent + already_sent_count
            )
            
            # Return statistics
            return {
                "total_users": len(users),
                "messages_sent": self._messages_sent,
                "messages_failed": self._messages_failed,
                "batches_completed": batches_completed,
                "already_sent": already_sent_count
            }
            
        finally:
            # Always deactivate power management
            self.power_manager.allow_sleep()
            self._is_running = False
    
    def stop_mailing(self) -> None:
        """
        Stop the mailing campaign gracefully.
        
        Sets a flag that will cause the mailing loop to stop after
        the current message is sent. Progress is saved automatically.
        """
        self._should_stop = True
    
    def is_running(self) -> bool:
        """
        Check if mailing is currently running.
        
        Returns:
            bool: True if mailing is in progress, False otherwise
        """
        return self._is_running
    
    def get_statistics(self) -> dict:
        """
        Get current mailing statistics.
        
        Returns:
            dict: Statistics with keys:
                - messages_sent: Number of messages sent in current session
                - messages_failed: Number of failed messages in current session
                - current_batch: Current batch number
                - is_running: Whether mailing is currently running
        """
        return {
            "messages_sent": self._messages_sent,
            "messages_failed": self._messages_failed,
            "current_batch": self._current_batch,
            "is_running": self._is_running
        }
