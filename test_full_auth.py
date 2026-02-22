#!/usr/bin/env python3
"""
Test script for full Telegram authentication with provided credentials.
Tests the complete auth flow: send code -> enter code -> verify.
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

# Test credentials
PHONE_CODE_HASH = "30e55188d7033e87febc0903c6b48c6426121943"
PHONE_NUMBER = "+79059341594"

# API Credentials (same as in app)
#API_ID = "26121943"
#API_HASH = "30e55188d7033e87febc0903c6b48c64"

API_ID = "22937843"
API_HASH = "f059dadbb0d4d4734feb75dd4fdcb4b9"

async def test_full_authentication():
    """Test complete authentication flow."""
    
    # Ensure directories exist
    ensure_app_directories()
    
    # Initialize error logger
    error_logger = ErrorLogger()
    
    print("=" * 60)
    print("Telegram Full Authentication Test")
    print("=" * 60)
    print()
    
    print(f"Phone Number: {PHONE_NUMBER}")
    print(f"Phone Code Hash: {PHONE_CODE_HASH[:20]}...")
    print(f"API ID: {API_ID}")
    print(f"API Hash: {API_HASH[:10]}...")
    print()
    
    # Initialize Telegram service
    telegram_service = TelegramService(
        api_id=API_ID,
        api_hash=API_HASH
    )
    
    try:
        # Step 1: Connect
        print("📡 Step 1: Connecting to Telegram...")
        await telegram_service.connect()
        print("✓ Connected successfully")
        print()
        
        # Step 2: Check if already authorized
        print("🔍 Step 2: Checking authorization status...")
        is_authorized = await telegram_service.is_authorized()
        
        if is_authorized:
            print("✓ Already authorized!")
            me = await telegram_service.client.get_me()
            print(f"  User: {me.first_name} {me.last_name or ''}")
            print(f"  Phone: {me.phone}")
            print(f"  ID: {me.id}")
            print()
            print("✅ TEST PASSED: Session is valid and authorized")
            return
        
        print("⚠ Not authorized yet")
        print()
        
        # Step 3: Send code request
        print("📤 Step 3: Sending code request...")
        try:
            phone_code_hash = await telegram_service.send_code_request(PHONE_NUMBER)
            print(f"✓ Code sent successfully!")
            print(f"  Phone code hash: {phone_code_hash[:20]}...")
            print()
            
            # Update the hash if it's different
            if phone_code_hash != PHONE_CODE_HASH:
                print(f"⚠ Note: New phone code hash received")
                print(f"  Old: {PHONE_CODE_HASH[:20]}...")
                print(f"  New: {phone_code_hash[:20]}...")
                print()
        except PhoneNumberInvalidError:
            print("❌ Invalid phone number format")
            print("   Phone must be in international format: +79137619949")
            return
        except Exception as e:
            print(f"❌ Failed to send code: {type(e).__name__}")
            print(f"   {str(e)}")
            error_logger.log_telegram_error(e, context={'phone': PHONE_NUMBER})
            return
        
        # Step 4: Get code from user
        print("📥 Step 4: Enter the code from Telegram")
        print("   (Check your Telegram app or SMS)")
        print()
        
        code = input("Enter the 5-digit code: ").strip()
        
        if not code:
            print("❌ No code entered")
            return
        
        print()
        print(f"🔐 Step 5: Verifying code: {code}")
        
        try:
            # Try to sign in with the code
            await telegram_service.sign_in(
                phone=PHONE_NUMBER,
                code=code,
                phone_code_hash=phone_code_hash
            )
            
            print("✓ Code verified successfully!")
            print()
            
            # Get user info
            me = await telegram_service.client.get_me()
            print("✅ AUTHENTICATION SUCCESSFUL!")
            print()
            print(f"User Information:")
            print(f"  Name: {me.first_name} {me.last_name or ''}")
            print(f"  Phone: {me.phone}")
            print(f"  Username: @{me.username}" if me.username else "  Username: (not set)")
            print(f"  User ID: {me.id}")
            print()
            print("✅ TEST PASSED: Full authentication completed")
            
        except PhoneCodeInvalidError:
            print("❌ Invalid code entered")
            print("   The code you entered is incorrect")
            return
            
        except PhoneCodeExpiredError:
            print("❌ Code expired")
            print("   Please request a new code")
            return
            
        except SessionPasswordNeededError:
            print("⚠ Two-factor authentication enabled")
            print()
            password = input("Enter your 2FA password: ").strip()
            
            if not password:
                print("❌ No password entered")
                return
            
            try:
                await telegram_service.client.sign_in(password=password)
                print("✓ 2FA password verified!")
                
                me = await telegram_service.client.get_me()
                print()
                print("✅ AUTHENTICATION SUCCESSFUL!")
                print()
                print(f"User Information:")
                print(f"  Name: {me.first_name} {me.last_name or ''}")
                print(f"  Phone: {me.phone}")
                print(f"  Username: @{me.username}" if me.username else "  Username: (not set)")
                print(f"  User ID: {me.id}")
                print()
                print("✅ TEST PASSED: Full authentication with 2FA completed")
                
            except Exception as e:
                print(f"❌ 2FA verification failed: {type(e).__name__}")
                print(f"   {str(e)}")
                error_logger.log_telegram_error(e, context={'phone': PHONE_NUMBER})
                return
        
        except Exception as e:
            print(f"❌ Sign in failed: {type(e).__name__}")
            print(f"   {str(e)}")
            error_logger.log_telegram_error(
                error=e,
                context={
                    'phone': PHONE_NUMBER,
                    'code': code,
                    'test': 'full_authentication'
                }
            )
            return
        
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}")
        print(f"   {str(e)}")
        
        error_logger.log_telegram_error(
            error=e,
            context={
                'phone': PHONE_NUMBER,
                'test': 'full_authentication'
            }
        )
        
        print()
        print(f"📝 Error logged to: {error_logger.get_log_path()}")
        
    finally:
        print()
        print("🔌 Disconnecting...")
        await telegram_service.disconnect()
        print("✓ Disconnected")
        print()
        print("=" * 60)


async def test_existing_session():
    """Quick test to check if session already exists and is valid."""
    
    print("=" * 60)
    print("Quick Session Check")
    print("=" * 60)
    print()
    
    telegram_service = TelegramService(
        api_id=API_ID,
        api_hash=API_HASH
    )
    
    try:
        await telegram_service.connect()
        is_authorized = await telegram_service.is_authorized()
        
        if is_authorized:
            me = await telegram_service.client.get_me()
            print("✅ Session is valid and authorized!")
            print()
            print(f"User: {me.first_name} {me.last_name or ''}")
            print(f"Phone: {me.phone}")
            print(f"ID: {me.id}")
            print()
            return True
        else:
            print("⚠ No valid session found")
            print("  Full authentication required")
            print()
            return False
            
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        return False
        
    finally:
        await telegram_service.disconnect()
        print("=" * 60)
        print()


def main():
    """Main entry point."""
    
    print()
    print("Choose test mode:")
    print("1. Quick session check (recommended first)")
    print("2. Full authentication test")
    print()
    
    choice = input("Enter choice (1 or 2): ").strip()
    print()
    
    if choice == "1":
        # Quick check
        session_valid = asyncio.run(test_existing_session())
        
        if not session_valid:
            print("Run option 2 for full authentication")
            
    elif choice == "2":
        # Full auth test
        asyncio.run(test_full_authentication())
        
    else:
        print("Invalid choice. Please run again and select 1 or 2.")


if __name__ == "__main__":
    main()
