"""
Demo script for MailingService.

Shows how to use the MailingService to coordinate a complete mailing campaign
with batch processing, delays, progress tracking, and error handling.
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path

from telegram.telegram_service import TelegramService
from telegram.mailing_service import MailingService
from telegram.models import User
from utils.progress_tracker import ProgressTracker
from utils.delay_calculator import DelayCalculator
from utils.error_logger import ErrorLogger
from utils.power_manager import PowerManager
from utils.constants import ensure_app_directories


async def progress_callback(user: User, result):
    """
    Callback function called after each message is sent.
    
    Args:
        user: The user who was sent a message
        result: SendResult with success status and error details
    """
    if result.success:
        if result.error:
            print(f"✓ Skipped {user.first_name} (ID: {user.id}): {result.error}")
        else:
            print(f"✓ Sent to {user.first_name} (ID: {user.id})")
    else:
        print(f"✗ Failed to send to {user.first_name} (ID: {user.id}): {result.error}")


def batch_callback(delay_seconds: float):
    """
    Callback function called when waiting between batches.
    
    Args:
        delay_seconds: Number of seconds to wait
    """
    delay_hours = delay_seconds / 3600
    print(f"\n⏳ Batch complete! Waiting {delay_hours:.2f} hours before next batch...\n")


async def main():
    """Main demo function."""
    print("=" * 60)
    print("Telegram Mailer - MailingService Demo")
    print("=" * 60)
    
    # Ensure app directories exist
    app_dir = ensure_app_directories()
    print(f"\n📁 App directory: {app_dir}")
    
    # Initialize services (conceptual - not actually connecting)
    print("\n🔧 Initializing services (demo mode)...")
    
    # Note: In a real application, you would:
    # 1. Get API credentials from ConfigManager
    # 2. Initialize TelegramService with real credentials
    # 3. Connect to Telegram and authenticate
    
    # For demo purposes, we'll just show the structure
    print("   - TelegramService (for Telegram API)")
    print("   - ProgressTracker (for saving progress)")
    print("   - DelayCalculator (for calculating delays)")
    print("   - ErrorLogger (for logging errors)")
    print("   - PowerManager (for preventing sleep)")
    print("   - MailingService (coordinates everything)")
    
    progress_tracker = ProgressTracker(app_dir)
    delay_calculator = DelayCalculator(batch_size=18)
    error_logger = ErrorLogger(app_dir)
    
    print("✓ Services initialized (demo mode)")
    
    # Example: Create sample users (in real app, get from telegram_service.get_group_members)
    print("\n👥 Creating sample users...")
    users = []
    for i in range(50):
        user = User(
            id=1000 + i,
            username=f"user{i}",
            first_name=f"User{i}",
            last_name=f"Last{i}",
            sent=False
        )
        users.append(user)
    print(f"✓ Created {len(users)} sample users")
    
    # Example message with HTML formatting
    message = """
<b>Hello!</b>

This is a <i>test message</i> from the Telegram Mailer.

<a href="https://example.com">Click here</a> for more info.
    """.strip()
    
    print(f"\n📝 Message prepared ({len(message)} characters)")
    
    # Set end date (7 days from now)
    end_date = datetime.now() + timedelta(days=7)
    print(f"\n📅 Target completion date: {end_date.strftime('%Y-%m-%d %H:%M')}")
    
    # Calculate delay
    delay_result = delay_calculator.calculate_delay(
        total_users=len(users),
        end_date=end_date
    )
    
    print(f"\n⏱️  Delay calculation:")
    print(f"   - Batches: {delay_result.num_batches}")
    print(f"   - Delay between batches: {delay_result.delay_hours:.2f} hours")
    print(f"   - Estimated completion: {delay_result.estimated_completion.strftime('%Y-%m-%d %H:%M')}")
    print(f"   - Safe: {'✓' if delay_result.is_safe else '✗'}")
    if delay_result.warning:
        print(f"   - Warning: {delay_result.warning}")
    
    # Note: In a real application, you would connect to Telegram first
    # await telegram_service.connect()
    # if not await telegram_service.is_authorized():
    #     # Handle authentication...
    #     pass
    
    print("\n" + "=" * 60)
    print("Starting mailing campaign...")
    print("=" * 60)
    
    # Start mailing (commented out for demo - would actually send messages)
    # result = await mailing_service.start_mailing(
    #     users=users,
    #     message=message,
    #     group_url="https://t.me/yourgroup",
    #     end_date=end_date,
    #     progress_callback=progress_callback,
    #     batch_callback=batch_callback
    # )
    
    # Simulate result for demo
    result = {
        "total_users": len(users),
        "messages_sent": 50,
        "messages_failed": 0,
        "batches_completed": 3,
        "already_sent": 0
    }
    
    print("\n" + "=" * 60)
    print("Mailing campaign completed!")
    print("=" * 60)
    print(f"\n📊 Final statistics:")
    print(f"   - Total users: {result['total_users']}")
    print(f"   - Messages sent: {result['messages_sent']}")
    print(f"   - Messages failed: {result['messages_failed']}")
    print(f"   - Batches completed: {result['batches_completed']}")
    print(f"   - Already sent (resumed): {result['already_sent']}")
    
    # Show error log location
    error_log_path = error_logger.get_log_path()
    print(f"\n📄 Error log: {error_log_path}")
    
    # Show progress file location
    print(f"📄 Progress files: {app_dir}/progress_*.txt")
    
    print("\n✓ Demo complete!")


async def demo_resume():
    """
    Demo showing how to resume a mailing campaign after interruption.
    """
    print("\n" + "=" * 60)
    print("Resume Demo")
    print("=" * 60)
    
    app_dir = ensure_app_directories()
    
    # Initialize services (demo mode)
    print("\n🔧 Initializing services (demo mode)...")
    progress_tracker = ProgressTracker(app_dir)
    
    # Create sample users
    users = []
    for i in range(50):
        user = User(
            id=1000 + i,
            username=f"user{i}",
            first_name=f"User{i}",
            last_name=f"Last{i}"
        )
        users.append(user)
    
    # Simulate previous progress (first 20 users already sent)
    print("\n📋 Loading previous progress...")
    progress_tracker.load_progress("https://t.me/testgroup")
    for i in range(20):
        progress_tracker.mark_sent(users[i].id)
    
    print(f"✓ Found {len(progress_tracker.sent_users)} users already sent")
    
    # Resume mailing - will automatically skip the first 20 users
    print("\n🔄 Resuming mailing campaign...")
    print("   (Will skip users 0-19 and continue from user 20)")
    
    # In real app, would call:
    # result = await mailing_service.start_mailing(
    #     users=users,
    #     message="Test message",
    #     group_url="https://t.me/testgroup",
    #     progress_callback=progress_callback
    # )
    
    print("\n✓ Resume demo complete!")


async def demo_stop():
    """
    Demo showing how to stop a mailing campaign gracefully.
    """
    print("\n" + "=" * 60)
    print("Stop Demo")
    print("=" * 60)
    
    print("\n💡 To stop a mailing campaign gracefully:")
    print("   1. Call mailing_service.stop_mailing()")
    print("   2. The service will finish sending the current message")
    print("   3. Progress is saved automatically")
    print("   4. Power management is deactivated")
    print("   5. You can resume later from where it stopped")
    
    print("\n📝 Example code:")
    print("""
    # Start mailing in background
    task = asyncio.create_task(
        mailing_service.start_mailing(
            users=users,
            message=message,
            group_url=group_url
        )
    )
    
    # Later, to stop gracefully:
    mailing_service.stop_mailing()
    
    # Wait for completion
    result = await task
    """)
    
    print("\n✓ Stop demo complete!")


if __name__ == "__main__":
    print("\n🚀 Running MailingService demos...\n")
    
    # Run main demo
    asyncio.run(main())
    
    # Run resume demo
    asyncio.run(demo_resume())
    
    # Run stop demo
    asyncio.run(demo_stop())
    
    print("\n" + "=" * 60)
    print("All demos complete!")
    print("=" * 60)
