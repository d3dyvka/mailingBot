"""
Demo script for DelayCalculator and ErrorLogger.

Shows how to use the delay calculator to plan a mailing campaign
and how to log errors during the process.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from utils.delay_calculator import DelayCalculator
from utils.error_logger import ErrorLogger
import tempfile


def demo_delay_calculator():
    """Demonstrate DelayCalculator usage."""
    print("=" * 60)
    print("DelayCalculator Demo")
    print("=" * 60)
    
    calculator = DelayCalculator()
    
    # Example 1: Calculate delay for a 10-day campaign with 100 users
    print("\n1. Calculate delay for 100 users over 10 days:")
    start_date = datetime.now()
    end_date = start_date + timedelta(days=10)
    total_users = 100
    
    result = calculator.calculate_delay(total_users, end_date, start_date)
    print(f"   Total users: {total_users}")
    print(f"   Number of batches: {result.num_batches}")
    print(f"   Delay between batches: {result.delay_hours:.2f} hours")
    print(f"   Is safe (>= 20h): {result.is_safe}")
    print(f"   Estimated completion: {result.estimated_completion.strftime('%Y-%m-%d %H:%M')}")
    if result.warning:
        print(f"   ⚠️  Warning: {result.warning}")
    
    # Example 2: Calculate delay for a tight deadline
    print("\n2. Calculate delay for 36 users over 1 day (tight deadline):")
    end_date = start_date + timedelta(days=1)
    total_users = 36
    
    result = calculator.calculate_delay(total_users, end_date, start_date)
    print(f"   Total users: {total_users}")
    print(f"   Number of batches: {result.num_batches}")
    print(f"   Delay between batches: {result.delay_hours:.2f} hours")
    print(f"   Is safe (>= 20h): {result.is_safe}")
    if result.warning:
        print(f"   ⚠️  Warning: {result.warning}")
    
    # Example 3: Calculate delay for a long campaign (will be capped at 24h)
    print("\n3. Calculate delay for 36 users over 60 days (long campaign):")
    end_date = start_date + timedelta(days=60)
    total_users = 36
    
    result = calculator.calculate_delay(total_users, end_date, start_date)
    print(f"   Total users: {total_users}")
    print(f"   Number of batches: {result.num_batches}")
    print(f"   Delay between batches: {result.delay_hours:.2f} hours")
    print(f"   Is safe (>= 20h): {result.is_safe}")
    if result.warning:
        print(f"   ⚠️  Warning: {result.warning}")
    
    # Example 4: Validate a specific delay
    print("\n4. Validate specific delays:")
    delays = [15.0, 20.0, 24.0, 30.0]
    for delay in delays:
        is_valid = calculator.validate_delay(delay)
        status = "✓ Valid" if is_valid else "✗ Invalid"
        print(f"   {delay}h: {status}")
    
    # Example 5: Estimate completion date with a specific delay
    print("\n5. Estimate completion date with 22-hour delay:")
    total_users = 54  # 3 batches
    delay_hours = 22.0
    
    completion = calculator.estimate_completion_date(
        total_users, delay_hours, start_date
    )
    print(f"   Total users: {total_users}")
    print(f"   Delay: {delay_hours} hours")
    print(f"   Estimated completion: {completion.strftime('%Y-%m-%d %H:%M')}")
    duration = completion - start_date
    print(f"   Total duration: {duration.total_seconds() / 3600:.2f} hours")


def demo_error_logger():
    """Demonstrate ErrorLogger usage."""
    print("\n" + "=" * 60)
    print("ErrorLogger Demo")
    print("=" * 60)
    
    # Use temporary directory for demo
    temp_dir = Path(tempfile.mkdtemp())
    logger = ErrorLogger(log_dir=temp_dir)
    
    print(f"\nLog file location: {logger.get_log_path()}")
    
    # Example 1: Log a basic error
    print("\n1. Log a basic error:")
    logger.log_error("ConnectionError", "Failed to connect to Telegram API")
    print("   ✓ Error logged")
    
    # Example 2: Log an error with context
    print("\n2. Log an error with context:")
    context = {
        "group": "https://t.me/testgroup",
        "batch": 2,
        "attempt": 1
    }
    logger.log_error("TimeoutError", "Request timed out after 30 seconds", context)
    print("   ✓ Error with context logged")
    
    # Example 3: Log a Telegram-specific error
    print("\n3. Log a Telegram error with user ID:")
    error = ValueError("User privacy settings prevent message delivery")
    logger.log_telegram_error(error, user_id=123456)
    print("   ✓ Telegram error logged")
    
    # Example 4: Log a FloodWait-like error
    print("\n4. Log a FloodWait error:")
    
    class MockFloodWaitError(Exception):
        def __init__(self, message, seconds):
            super().__init__(message)
            self.seconds = seconds
    
    flood_error = MockFloodWaitError("Too many requests", 3600)
    logger.log_telegram_error(
        flood_error,
        user_id=789012,
        context={"batch": 3, "message_count": 18}
    )
    print("   ✓ FloodWait error logged")
    
    # Example 5: Check error count
    print(f"\n5. Total errors logged: {logger.get_error_count()}")
    
    # Example 6: Read the log
    print("\n6. Log file contents:")
    print("-" * 60)
    log_content = logger.read_log()
    print(log_content)
    print("-" * 60)
    
    # Clean up
    import shutil
    shutil.rmtree(temp_dir)
    print("\n✓ Demo completed, temporary files cleaned up")


def demo_combined_usage():
    """Demonstrate using both classes together in a realistic scenario."""
    print("\n" + "=" * 60)
    print("Combined Usage Demo: Planning a Mailing Campaign")
    print("=" * 60)
    
    # Initialize components
    calculator = DelayCalculator()
    temp_dir = Path(tempfile.mkdtemp())
    logger = ErrorLogger(log_dir=temp_dir)
    
    # Scenario: Plan a campaign for 180 users over 7 days
    print("\nScenario: Mailing campaign for 180 users")
    print("-" * 60)
    
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    total_users = 180
    
    print(f"Start date: {start_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"End date: {end_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"Total users: {total_users}")
    
    # Calculate optimal delay
    try:
        result = calculator.calculate_delay(total_users, end_date, start_date)
        
        print(f"\nCalculation results:")
        print(f"  • Number of batches: {result.num_batches}")
        print(f"  • Delay between batches: {result.delay_hours:.2f} hours")
        print(f"  • Safety check: {'✓ Safe' if result.is_safe else '✗ Unsafe'}")
        print(f"  • Estimated completion: {result.estimated_completion.strftime('%Y-%m-%d %H:%M')}")
        
        if result.warning:
            print(f"\n⚠️  Warning: {result.warning}")
            logger.log_error(
                "DelayWarning",
                result.warning,
                {
                    "total_users": total_users,
                    "num_batches": result.num_batches,
                    "delay_hours": result.delay_hours
                }
            )
        
        # Validate the delay
        if not calculator.validate_delay(result.delay_hours):
            print("\n⚠️  Delay is below minimum safe threshold!")
            logger.log_error(
                "UnsafeDelay",
                f"Calculated delay ({result.delay_hours:.2f}h) is below minimum safe delay (20h)",
                {
                    "calculated_delay": result.delay_hours,
                    "min_safe_delay": 20,
                    "recommendation": "Consider extending the end date or reducing user count"
                }
            )
        
    except ValueError as e:
        print(f"\n✗ Error calculating delay: {e}")
        logger.log_telegram_error(e, context={"total_users": total_users})
    
    # Show logged errors if any
    if logger.get_error_count() > 0:
        print(f"\n{logger.get_error_count()} warning(s) logged to: {logger.get_log_path()}")
    
    # Clean up
    import shutil
    shutil.rmtree(temp_dir)
    print("\n✓ Demo completed")


if __name__ == "__main__":
    demo_delay_calculator()
    demo_error_logger()
    demo_combined_usage()
    
    print("\n" + "=" * 60)
    print("All demos completed successfully!")
    print("=" * 60)
