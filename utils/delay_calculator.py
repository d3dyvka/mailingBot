"""
Delay Calculator for Telegram Mailer MacOS App.

Calculates optimal delays between batches based on end date and user count.
Ensures delays stay within safe limits (20-24 hours).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from math import ceil

from .constants import DEFAULT_BATCH_SIZE, MIN_SAFE_DELAY_HOURS, MAX_DELAY_HOURS


@dataclass
class DelayResult:
    """
    Result of delay calculation.
    
    Attributes:
        delay_hours: Calculated delay between batches in hours
        num_batches: Number of batches required
        estimated_completion: Estimated completion date
        is_safe: True if delay >= MIN_SAFE_DELAY_HOURS
        warning: Warning message if delay is unsafe or capped (optional)
    """
    delay_hours: float
    num_batches: int
    estimated_completion: datetime
    is_safe: bool
    warning: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of the delay result."""
        result = f"Delay: {self.delay_hours:.2f} hours, Batches: {self.num_batches}"
        result += f"\nEstimated completion: {self.estimated_completion.strftime('%Y-%m-%d %H:%M')}"
        if self.warning:
            result += f"\nWarning: {self.warning}"
        return result


class DelayCalculator:
    """
    Calculates optimal delays between message batches.
    
    The calculator determines the best delay between batches to complete
    a mailing campaign by a specified end date, while respecting safety
    constraints (minimum 20 hours, maximum 24 hours).
    
    Attributes:
        batch_size: Number of people per batch (default: 18)
    """
    
    def __init__(self, batch_size: int = DEFAULT_BATCH_SIZE):
        """
        Initialize the delay calculator.
        
        Args:
            batch_size: Number of people in one batch (default: 18)
        """
        self.batch_size = batch_size
    
    def calculate_delay(
        self,
        total_users: int,
        end_date: datetime,
        start_date: Optional[datetime] = None
    ) -> DelayResult:
        """
        Calculate optimal delay between batches.
        
        Formula: (available_hours / number_of_batches)
        
        IMPORTANT:
        - Batch size is always 18 PEOPLE (not hours!)
        - Maximum delay is capped at 24 hours
        - Minimum safe delay is 20 hours
        
        Args:
            total_users: Total number of users (obtained automatically from Telegram API)
            end_date: Target completion date
            start_date: Start date (defaults to current time)
            
        Returns:
            DelayResult: Result with calculated delay and metadata
            
        Raises:
            ValueError: If total_users <= 0 or end_date is in the past
        """
        # Validation
        if total_users <= 0:
            raise ValueError("total_users must be greater than 0")
        
        if start_date is None:
            start_date = datetime.now()
        
        if end_date <= start_date:
            raise ValueError("end_date must be after start_date")
        
        # Calculate number of batches
        # Batch size is always 18 PEOPLE
        num_batches = ceil(total_users / self.batch_size)
        
        # Calculate available time in hours
        time_delta = end_date - start_date
        available_hours = time_delta.total_seconds() / 3600
        
        # Time to send one batch (18 messages * 30 sec average = 9 minutes = 0.15 hours)
        batch_send_time = 0.15  # hours
        
        # Total time needed for sending all batches
        total_send_time = num_batches * batch_send_time
        
        # Available time for delays between batches
        available_delay_time = available_hours - total_send_time
        
        # Calculate optimal delay between batches
        # We need (num_batches - 1) delays between num_batches batches
        if num_batches == 1:
            # Only one batch, no delay needed
            optimal_delay = 0
        else:
            optimal_delay = available_delay_time / (num_batches - 1)
        
        # IMPORTANT: Cap delay at maximum 24 hours
        warning = None
        if optimal_delay > MAX_DELAY_HOURS:
            warning = f"Calculated delay ({optimal_delay:.2f}h) exceeds maximum. Capped at {MAX_DELAY_HOURS}h."
            optimal_delay = MAX_DELAY_HOURS
        
        # Check if delay is safe (>= 20 hours)
        # Single batch is always safe since no delay is needed
        if num_batches == 1:
            is_safe = True
        else:
            is_safe = optimal_delay >= MIN_SAFE_DELAY_HOURS
            if not is_safe and warning is None:
                warning = f"Delay ({optimal_delay:.2f}h) is below minimum safe delay ({MIN_SAFE_DELAY_HOURS}h)."
        
        # Calculate estimated completion date with the actual delay
        # Total time = send time + delay time
        if num_batches == 1:
            estimated_total_hours = batch_send_time
        else:
            estimated_total_hours = total_send_time + (optimal_delay * (num_batches - 1))
        
        estimated_completion = start_date
        from datetime import timedelta
        estimated_completion = start_date + timedelta(hours=estimated_total_hours)
        
        return DelayResult(
            delay_hours=optimal_delay,
            num_batches=num_batches,
            estimated_completion=estimated_completion,
            is_safe=is_safe,
            warning=warning
        )
    
    def validate_delay(self, delay_hours: float) -> bool:
        """
        Validate that a delay meets minimum safety requirements.
        
        Args:
            delay_hours: Delay in hours to validate
            
        Returns:
            bool: True if delay >= MIN_SAFE_DELAY_HOURS
        """
        return delay_hours >= MIN_SAFE_DELAY_HOURS
    
    def estimate_completion_date(
        self,
        total_users: int,
        delay_hours: float,
        start_date: Optional[datetime] = None
    ) -> datetime:
        """
        Estimate completion date given a specific delay.
        
        Args:
            total_users: Total number of users
            delay_hours: Delay between batches in hours
            start_date: Start date (defaults to current time)
            
        Returns:
            datetime: Estimated completion date
            
        Raises:
            ValueError: If total_users <= 0 or delay_hours < 0
        """
        if total_users <= 0:
            raise ValueError("total_users must be greater than 0")
        
        if delay_hours < 0:
            raise ValueError("delay_hours must be non-negative")
        
        if start_date is None:
            start_date = datetime.now()
        
        # Calculate number of batches
        num_batches = ceil(total_users / self.batch_size)
        
        # Time to send one batch
        batch_send_time = 0.15  # hours
        
        # Total time = send time + delay time
        if num_batches == 1:
            total_hours = batch_send_time
        else:
            total_send_time = num_batches * batch_send_time
            total_delay_time = delay_hours * (num_batches - 1)
            total_hours = total_send_time + total_delay_time
        
        from datetime import timedelta
        return start_date + timedelta(hours=total_hours)
