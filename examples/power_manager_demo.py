"""
Demo script for PowerManager.

Demonstrates how to use PowerManager to prevent macOS from sleeping
during long-running operations like mailing campaigns.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from utils.power_manager import PowerManager


def demo_basic_usage():
    """Demonstrate basic PowerManager usage."""
    print("=== Basic PowerManager Usage ===\n")
    
    pm = PowerManager()
    
    print("1. Initial state:")
    print(f"   Sleep prevented: {pm.is_sleep_prevented()}")
    
    print("\n2. Activating sleep prevention...")
    pm.prevent_sleep()
    print(f"   Sleep prevented: {pm.is_sleep_prevented()}")
    print("   Your Mac will not sleep while this is active!")
    
    print("\n3. Simulating work (5 seconds)...")
    for i in range(5):
        time.sleep(1)
        print(f"   Working... {i+1}/5")
    
    print("\n4. Deactivating sleep prevention...")
    pm.allow_sleep()
    print(f"   Sleep prevented: {pm.is_sleep_prevented()}")
    print("   Your Mac can now sleep normally.")


def demo_context_manager():
    """Demonstrate PowerManager as context manager."""
    print("\n\n=== Context Manager Usage ===\n")
    
    print("Using PowerManager with 'with' statement:")
    print("Sleep prevention will be automatic!\n")
    
    with PowerManager() as pm:
        print(f"Inside context: Sleep prevented = {pm.is_sleep_prevented()}")
        print("Simulating work (3 seconds)...")
        time.sleep(3)
        print("Work complete!")
    
    print(f"Outside context: Sleep prevented = {pm.is_sleep_prevented()}")
    print("Sleep prevention automatically deactivated!")


def demo_mailing_simulation():
    """Simulate a mailing campaign with sleep prevention."""
    print("\n\n=== Mailing Campaign Simulation ===\n")
    
    # Simulate sending messages to users
    users = [f"User_{i}" for i in range(1, 11)]
    
    print(f"Starting mailing campaign to {len(users)} users...")
    print("Sleep prevention will be active during the campaign.\n")
    
    with PowerManager() as pm:
        print(f"Sleep prevention: {pm.is_sleep_prevented()}")
        
        for i, user in enumerate(users, 1):
            print(f"[{i}/{len(users)}] Sending message to {user}...")
            time.sleep(0.5)  # Simulate message sending
        
        print("\nAll messages sent!")
    
    print(f"Sleep prevention: {pm.is_sleep_prevented()}")
    print("Campaign complete. Mac can sleep normally now.")


def demo_error_handling():
    """Demonstrate error handling with PowerManager."""
    print("\n\n=== Error Handling ===\n")
    
    print("PowerManager handles errors gracefully:")
    
    with PowerManager() as pm:
        print(f"Sleep prevented: {pm.is_sleep_prevented()}")
        
        try:
            print("Simulating an error during operation...")
            time.sleep(1)
            raise ValueError("Simulated error!")
        except ValueError as e:
            print(f"Error occurred: {e}")
    
    print(f"Sleep prevented: {pm.is_sleep_prevented()}")
    print("Sleep prevention was deactivated despite the error!")


def demo_multiple_instances():
    """Demonstrate multiple PowerManager instances."""
    print("\n\n=== Multiple Instances ===\n")
    
    print("Creating two independent PowerManager instances:\n")
    
    pm1 = PowerManager()
    pm2 = PowerManager()
    
    print("Activating pm1...")
    pm1.prevent_sleep()
    print(f"pm1 sleep prevented: {pm1.is_sleep_prevented()}")
    print(f"pm2 sleep prevented: {pm2.is_sleep_prevented()}")
    
    print("\nActivating pm2...")
    pm2.prevent_sleep()
    print(f"pm1 sleep prevented: {pm1.is_sleep_prevented()}")
    print(f"pm2 sleep prevented: {pm2.is_sleep_prevented()}")
    
    print("\nDeactivating pm1...")
    pm1.allow_sleep()
    print(f"pm1 sleep prevented: {pm1.is_sleep_prevented()}")
    print(f"pm2 sleep prevented: {pm2.is_sleep_prevented()}")
    
    print("\nDeactivating pm2...")
    pm2.allow_sleep()
    print(f"pm1 sleep prevented: {pm1.is_sleep_prevented()}")
    print(f"pm2 sleep prevented: {pm2.is_sleep_prevented()}")
    
    print("\nBoth instances are independent!")


def demo_idempotent_calls():
    """Demonstrate idempotent behavior."""
    print("\n\n=== Idempotent Calls ===\n")
    
    pm = PowerManager()
    
    print("Calling prevent_sleep() multiple times:")
    pm.prevent_sleep()
    print(f"  After 1st call: {pm.is_sleep_prevented()}")
    pm.prevent_sleep()
    print(f"  After 2nd call: {pm.is_sleep_prevented()}")
    pm.prevent_sleep()
    print(f"  After 3rd call: {pm.is_sleep_prevented()}")
    print("  Safe to call multiple times!\n")
    
    print("Calling allow_sleep() multiple times:")
    pm.allow_sleep()
    print(f"  After 1st call: {pm.is_sleep_prevented()}")
    pm.allow_sleep()
    print(f"  After 2nd call: {pm.is_sleep_prevented()}")
    pm.allow_sleep()
    print(f"  After 3rd call: {pm.is_sleep_prevented()}")
    print("  Safe to call multiple times!")


def main():
    """Run all demos."""
    print("=" * 60)
    print("PowerManager Demo")
    print("=" * 60)
    
    try:
        demo_basic_usage()
        demo_context_manager()
        demo_mailing_simulation()
        demo_error_handling()
        demo_multiple_instances()
        demo_idempotent_calls()
        
        print("\n" + "=" * 60)
        print("All demos completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError running demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

