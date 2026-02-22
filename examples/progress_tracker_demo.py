"""
Demo script for Progress Tracker.

This script demonstrates the basic usage of the ProgressTracker class
for tracking Telegram mailing progress with append-only file logic.
"""

from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.progress_tracker import ProgressTracker
from utils.constants import PROGRESS_DIR, ensure_app_directories


def demo_basic_usage():
    """Demonstrate basic ProgressTracker usage."""
    print("=" * 60)
    print("Progress Tracker Demo - Basic Usage")
    print("=" * 60)
    
    # Ensure directories exist
    ensure_app_directories()
    
    # Create tracker
    tracker = ProgressTracker(PROGRESS_DIR)
    
    # Load progress for a group
    group_url = "https://t.me/demo_group"
    print(f"\n1. Loading progress for group: {group_url}")
    tracker.load_progress(group_url)
    print(f"   Progress file: {tracker.progress_file}")
    print(f"   Previously sent users: {len(tracker.sent_users)}")
    
    # Set total users
    total_users = 50
    tracker.set_total_users(total_users)
    print(f"\n2. Set total users: {total_users}")
    
    # Simulate sending messages
    print("\n3. Simulating message sending...")
    batch_size = 18
    for i in range(1, batch_size + 1):
        user_id = 1000 + i
        tracker.mark_sent(user_id)
        print(f"   Sent message to user {user_id}")
    
    # Get statistics
    stats = tracker.get_statistics()
    print(f"\n4. Statistics:")
    print(f"   Sent: {stats['sent']}")
    print(f"   Remaining: {stats['remaining']}")
    print(f"   Total: {stats['total']}")
    
    # Update summary
    tracker.update_summary(total_users=total_users, sent_count=stats['sent'])
    print(f"\n5. Summary updated in progress file")
    
    # Show file content
    print(f"\n6. Progress file content (first 20 lines):")
    with open(tracker.progress_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()[:20]
        for line in lines:
            print(f"   {line.rstrip()}")
    
    print("\n" + "=" * 60)


def demo_resume_after_restart():
    """Demonstrate resuming progress after application restart."""
    print("\n" + "=" * 60)
    print("Progress Tracker Demo - Resume After Restart")
    print("=" * 60)
    
    # Ensure directories exist
    ensure_app_directories()
    
    group_url = "https://t.me/demo_group"
    
    # Simulate first session
    print("\n1. First session - sending to first batch")
    tracker1 = ProgressTracker(PROGRESS_DIR)
    tracker1.load_progress(group_url)
    tracker1.set_total_users(50)
    
    for i in range(1, 19):  # First batch: 18 users
        tracker1.mark_sent(1000 + i)
    
    stats1 = tracker1.get_statistics()
    print(f"   Sent: {stats1['sent']}, Remaining: {stats1['remaining']}")
    
    # Simulate application restart
    print("\n2. Application restart - creating new tracker")
    tracker2 = ProgressTracker(PROGRESS_DIR)
    tracker2.load_progress(group_url)
    tracker2.set_total_users(50)
    
    print(f"   Loaded previous progress: {len(tracker2.sent_users)} users")
    
    # Continue with second batch
    print("\n3. Second session - sending to second batch")
    for i in range(19, 37):  # Second batch: 18 users
        user_id = 1000 + i
        if not tracker2.is_sent(user_id):
            tracker2.mark_sent(user_id)
            print(f"   Sent message to user {user_id}")
        else:
            print(f"   Skipped user {user_id} (already sent)")
    
    stats2 = tracker2.get_statistics()
    print(f"\n4. Final statistics:")
    print(f"   Sent: {stats2['sent']}, Remaining: {stats2['remaining']}")
    
    print("\n" + "=" * 60)


def demo_multiple_groups():
    """Demonstrate tracking progress for multiple groups."""
    print("\n" + "=" * 60)
    print("Progress Tracker Demo - Multiple Groups")
    print("=" * 60)
    
    # Ensure directories exist
    ensure_app_directories()
    
    tracker = ProgressTracker(PROGRESS_DIR)
    
    # Group 1
    group1 = "https://t.me/group1"
    print(f"\n1. Sending to {group1}")
    tracker.load_progress(group1)
    for i in range(1, 6):
        tracker.mark_sent(i)
    print(f"   Sent to {len(tracker.sent_users)} users")
    
    # Group 2
    group2 = "https://t.me/group2"
    print(f"\n2. Sending to {group2}")
    tracker.load_progress(group2)
    for i in range(101, 106):
        tracker.mark_sent(i)
    print(f"   Sent to {len(tracker.sent_users)} users")
    
    # Verify independence
    print("\n3. Verifying independent progress:")
    tracker.load_progress(group1)
    print(f"   Group 1 has {len(tracker.sent_users)} sent users")
    print(f"   User 3 sent in group 1: {tracker.is_sent(3)}")
    print(f"   User 103 sent in group 1: {tracker.is_sent(103)}")
    
    tracker.load_progress(group2)
    print(f"   Group 2 has {len(tracker.sent_users)} sent users")
    print(f"   User 3 sent in group 2: {tracker.is_sent(3)}")
    print(f"   User 103 sent in group 2: {tracker.is_sent(103)}")
    
    print("\n" + "=" * 60)


def demo_reset_progress():
    """Demonstrate resetting progress for a new campaign."""
    print("\n" + "=" * 60)
    print("Progress Tracker Demo - Reset Progress")
    print("=" * 60)
    
    # Ensure directories exist
    ensure_app_directories()
    
    tracker = ProgressTracker(PROGRESS_DIR)
    group_url = "https://t.me/demo_reset_group"
    
    # Create some progress
    print("\n1. Creating initial progress")
    tracker.load_progress(group_url)
    for i in range(1, 11):
        tracker.mark_sent(i)
    print(f"   Sent to {len(tracker.sent_users)} users")
    
    # Reset progress
    print("\n2. Resetting progress for new campaign")
    tracker.reset_progress(group_url)
    print(f"   Progress reset complete")
    
    # Load again
    print("\n3. Loading progress after reset")
    tracker.load_progress(group_url)
    print(f"   Sent users: {len(tracker.sent_users)}")
    print(f"   Progress file exists: {tracker.progress_file.exists()}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TELEGRAM MAILER - PROGRESS TRACKER DEMO")
    print("=" * 60)
    
    # Run all demos
    demo_basic_usage()
    demo_resume_after_restart()
    demo_multiple_groups()
    demo_reset_progress()
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)
