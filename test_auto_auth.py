#!/usr/bin/env python3
"""
Automated authentication test with provided credentials.
This script will attempt to authenticate using the provided phone code hash.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from telegram.telegram_service import TelegramService
from utils.error_logger import ErrorLogger
from utils.constants import ensure_app_directories
from telethon.errors import (
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    SessionPasswordNeededError,
    PhoneNumberInvalidError
)

# Provided credentials
PHONE_NUMBER = "+79137619949"
PHONE_CODE_HASH = "30e55188d7033e87febc0903c6b48c6426121943"

# API Credentials
API_ID = "22937843"
API_HASH = "f059dadbb0d4d4734feb75dd4fdcb4b9"


async def test_authentication_with_code(code: str):
    """
    Test authentication with provided code.
    
    Args:
        code: The 5-digit code from Telegram
    """
    
    # Ensure directories exist
    ensure_app_directories()
    
    # Initialize error logger
    error_logger = ErrorLogger()
    
    print("=" * 70)
    print("Automated Telegram Authentication Test")
    print("=" * 70)
    print()
    
    print("Configuration:")
    print(f"  Phone Number: {PHONE_NUMBER}")
    print(f"  Phone Code Hash: {PHONE_CODE_HASH[:30]}...")
    print(f"  API ID: {API_ID}")
    print(f"  API Hash: {API_HASH[:15]}...")
    print(f"  Code: {code}")
    print()
    
    # Initialize Telegram service
    telegram_service = TelegramService(
        api_id=API_ID,
        api_hash=API_HASH
    )
    
    try:
        # Step 1: Connect
        print("📡 Connecting to Telegram...")
        await telegram_service.connect()
        print("✓ Connected")
        print()
        
        # Step 2: Check if already authorized
        print("🔍 Checking authorization status...")
        is_authorized = await telegram_service.is_authorized()
        
        if is_authorized:
            me = await telegram_service.client.get_me()
            print("✅ Already authorized!")
            print()
            print("User Information:")
            print(f"  Name: {me.first_name} {me.last_name or ''}")
            print(f"  Phone: {me.phone}")
            print(f"  Username: @{me.username}" if me.username else "  Username: (not set)")
            print(f"  User ID: {me.id}")
            print()
            print("=" * 70)
            return True
        
        print("⚠ Not authorized, proceeding with authentication...")
        print()
        
        # Step 3: Sign in with provided credentials
        print(f"🔐 Attempting to sign in with code: {code}")
        
        try:
            await telegram_service.sign_in(
                phone=PHONE_NUMBER,
                code=code,
                phone_code_hash=PHONE_CODE_HASH
            )
            
            print("✓ Code verified successfully!")
            print()
            
            # Get user info
            me = await telegram_service.client.get_me()
            print("✅ AUTHENTICATION SUCCESSFUL!")
            print()
            print("User Information:")
            print(f"  Name: {me.first_name} {me.last_name or ''}")
            print(f"  Phone: {me.phone}")
            print(f"  Username: @{me.username}" if me.username else "  Username: (not set)")
            print(f"  User ID: {me.id}")
            print()
            print("Session saved successfully!")
            print(f"Session file: ~/Library/Application Support/TelegramMailer/session_name.session")
            print()
            print("=" * 70)
            return True
            
        except PhoneCodeInvalidError:
            print("❌ FAILED: Invalid code")
            print()
            print("Possible reasons:")
            print("  1. The code is incorrect")
            print("  2. The code has expired (codes expire after a few minutes)")
            print("  3. The phone_code_hash is outdated")
            print()
            print("Solution:")
            print("  1. Request a new code by running the app or test_auth_code.py")
            print("  2. Use the new code immediately")
            print()
            return False
            
        except PhoneCodeExpiredError:
            print("❌ FAILED: Code expired")
            print()
            print("The authentication code has expired.")
            print("Please request a new code and try again immediately.")
            print()
            return False
            
        except SessionPasswordNeededError:
            print("⚠ Two-factor authentication (2FA) is enabled")
            print()
            print("This account requires a 2FA password.")
            print("Please run the interactive test (test_full_auth.py) to enter the password.")
            print()
            return False
            
        except Exception as e:
            print(f"❌ FAILED: {type(e).__name__}")
            print(f"   Error: {str(e)}")
            print()
            
            error_logger.log_telegram_error(
                error=e,
                context={
                    'phone': PHONE_NUMBER,
                    'code': code,
                    'phone_code_hash': PHONE_CODE_HASH[:30] + '...',
                    'test': 'automated_authentication'
                }
            )
            
            print(f"📝 Error logged to: {error_logger.get_log_path()}")
            print()
            return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}")
        print(f"   {str(e)}")
        print()
        
        error_logger.log_telegram_error(
            error=e,
            context={
                'phone': PHONE_NUMBER,
                'test': 'automated_authentication'
            }
        )
        
        print(f"📝 Error logged to: {error_logger.get_log_path()}")
        print()
        return False
        
    finally:
        print("🔌 Disconnecting...")
        await telegram_service.disconnect()
        print("✓ Disconnected")
        print()


def main():
    """Main entry point."""
    
    print()
    print("This script will attempt to authenticate using:")
    print(f"  Phone: {PHONE_NUMBER}")
    print(f"  Hash: {PHONE_CODE_HASH[:30]}...")
    print()
    print("⚠️  IMPORTANT:")
    print("  - The phone_code_hash may be expired")
    print("  - You need the current 5-digit code from Telegram")
    print("  - Codes expire after a few minutes")
    print()
    
    code = input("Enter the 5-digit code from Telegram (or 'q' to quit): ").strip()
    
    if code.lower() == 'q':
        print("Cancelled.")
        return
    
    if not code or len(code) != 5 or not code.isdigit():
        print()
        print("❌ Invalid code format. Code must be exactly 5 digits.")
        print("   Example: 12345")
        return
    
    print()
    
    # Run the authentication test
    success = asyncio.run(test_authentication_with_code(code))
    
    if success:
        print("✅ SUCCESS: You can now use the application!")
        print()
        print("Next steps:")
        print("  1. Launch the app: open /Applications/TelegramMailer.app")
        print("  2. The app will use the saved session automatically")
    else:
        print("❌ FAILED: Authentication was not successful")
        print()
        print("Next steps:")
        print("  1. Request a new code: python3 test_auth_code.py")
        print("  2. Run this script again with the new code")
        print("  3. Or use the interactive test: python3 test_full_auth.py")


if __name__ == "__main__":
    main()
