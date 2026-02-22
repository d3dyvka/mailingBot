#!/usr/bin/env python3
"""
Test Telegram authentication using Pyrogram instead of Telethon.
Pyrogram sometimes has better code delivery.
"""

import asyncio
from pathlib import Path

# Fix for Python 3.14 event loop issue
import sys
if sys.version_info >= (3, 10):
    try:
        asyncio.set_event_loop(asyncio.new_event_loop())
    except:
        pass

from pyrogram import Client
from pyrogram.errors import (
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PhoneNumberInvalid,
    BadRequest
)

# API Credentials
API_ID = "26121943"
API_HASH = "30e55188d7033e87febc0903c6b48c64"
PHONE_NUMBER = "+79137619949"

# Session directory
SESSION_DIR = Path.home() / "Library" / "Application Support" / "TelegramMailer"
SESSION_DIR.mkdir(parents=True, exist_ok=True)
SESSION_NAME = str(SESSION_DIR / "pyrogram_session")


async def test_authentication():
    """Test authentication with Pyrogram."""
    
    print("=" * 70)
    print("Pyrogram Authentication Test")
    print("=" * 70)
    print()
    
    print("Configuration:")
    print(f"  API_ID: {API_ID}")
    print(f"  API_HASH: {API_HASH[:15]}...")
    print(f"  Phone: {PHONE_NUMBER}")
    print(f"  Session: {SESSION_NAME}")
    print()
    
    # Create Pyrogram client
    app = Client(
        name=SESSION_NAME,
        api_id=API_ID,
        api_hash=API_HASH,
        phone_number=PHONE_NUMBER,
        workdir=str(SESSION_DIR)
    )
    
    try:
        print("📡 Connecting to Telegram...")
        await app.connect()
        print("✓ Connected")
        print()
        
        # Check if already authorized
        try:
            me = await app.get_me()
            print("✅ Already authorized!")
            print()
            
            print("User Information:")
            print(f"  Name: {me.first_name} {me.last_name or ''}")
            print(f"  Phone: {me.phone_number}")
            print(f"  Username: @{me.username}" if me.username else "  Username: (not set)")
            print(f"  User ID: {me.id}")
            print()
            
            await app.disconnect()
            return True
        except:
            # Not authorized, continue with auth flow
            pass
        
        print("⚠ Not authorized, starting authentication...")
        print()
        
        # Send code
        print("📤 Sending authentication code...")
        try:
            sent_code = await app.send_code(PHONE_NUMBER)
            print("✓ Code sent successfully!")
            print(f"  Phone code hash: {sent_code.phone_code_hash[:30]}...")
            print()
            
            # Check code type
            if hasattr(sent_code, 'type'):
                code_type = str(sent_code.type)
                print(f"📱 Code delivery method: {code_type}")
                
                if 'app' in code_type.lower():
                    print("   → Check your Telegram app")
                elif 'sms' in code_type.lower():
                    print("   → Check your SMS messages")
                elif 'call' in code_type.lower():
                    print("   → You will receive a phone call")
            
            print()
            print("⏱️  Waiting for code...")
            print("   Codes usually arrive within 10-30 seconds")
            print()
            
        except PhoneNumberInvalid:
            print("❌ Invalid phone number")
            print("   Make sure the number is in international format: +79137619949")
            await app.disconnect()
            return False
            
        except BadRequest as e:
            print(f"❌ Bad request: {e}")
            print()
            print("Possible reasons:")
            print("  1. Invalid API credentials")
            print("  2. Phone number format is wrong")
            print("  3. Too many requests (wait a few minutes)")
            await app.disconnect()
            return False
            
        except Exception as e:
            print(f"❌ Failed to send code: {type(e).__name__}")
            print(f"   {str(e)}")
            await app.disconnect()
            return False
        
        # Get code from user
        code = input("Enter the 5-digit code: ").strip()
        
        if not code or len(code) != 5:
            print()
            print("❌ Invalid code format")
            await app.disconnect()
            return False
        
        print()
        print(f"🔐 Verifying code: {code}")
        
        try:
            # Sign in with code
            await app.sign_in(PHONE_NUMBER, sent_code.phone_code_hash, code)
            
            print("✓ Code verified!")
            print()
            
            # Get user info
            me = await app.get_me()
            print("✅ AUTHENTICATION SUCCESSFUL!")
            print()
            print("User Information:")
            print(f"  Name: {me.first_name} {me.last_name or ''}")
            print(f"  Phone: {me.phone_number}")
            print(f"  Username: @{me.username}" if me.username else "  Username: (not set)")
            print(f"  User ID: {me.id}")
            print()
            print(f"Session saved to: {SESSION_NAME}.session")
            print()
            
            await app.disconnect()
            return True
            
        except PhoneCodeInvalid:
            print("❌ Invalid code")
            print("   The code you entered is incorrect")
            await app.disconnect()
            return False
            
        except PhoneCodeExpired:
            print("❌ Code expired")
            print("   Please run the script again to get a new code")
            await app.disconnect()
            return False
            
        except SessionPasswordNeeded:
            print("⚠ Two-factor authentication (2FA) enabled")
            print()
            
            password = input("Enter your 2FA password: ").strip()
            
            if not password:
                print("❌ No password entered")
                await app.disconnect()
                return False
            
            try:
                await app.check_password(password)
                print("✓ 2FA password verified!")
                print()
                
                me = await app.get_me()
                print("✅ AUTHENTICATION SUCCESSFUL!")
                print()
                print("User Information:")
                print(f"  Name: {me.first_name} {me.last_name or ''}")
                print(f"  Phone: {me.phone_number}")
                print(f"  Username: @{me.username}" if me.username else "  Username: (not set)")
                print(f"  User ID: {me.id}")
                print()
                
                await app.disconnect()
                return True
                
            except Exception as e:
                print(f"❌ 2FA verification failed: {type(e).__name__}")
                print(f"   {str(e)}")
                await app.disconnect()
                return False
        
        except Exception as e:
            print(f"❌ Sign in failed: {type(e).__name__}")
            print(f"   {str(e)}")
            await app.disconnect()
            return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}")
        print(f"   {str(e)}")
        
        try:
            await app.disconnect()
        except:
            pass
        
        return False
    
    finally:
        print()
        print("=" * 70)


async def quick_check():
    """Quick check if session exists and is valid."""
    
    print("=" * 70)
    print("Quick Session Check (Pyrogram)")
    print("=" * 70)
    print()
    
    app = Client(
        name=SESSION_NAME,
        api_id=API_ID,
        api_hash=API_HASH,
        workdir=str(SESSION_DIR)
    )
    
    try:
        await app.connect()
        
        try:
            me = await app.get_me()
            print("✅ Session is valid and authorized!")
            print()
            print(f"User: {me.first_name} {me.last_name or ''}")
            print(f"Phone: {me.phone_number}")
            print(f"ID: {me.id}")
            print()
            
            await app.disconnect()
            return True
        except:
            print("⚠ No valid session found")
            print("  Full authentication required")
            print()
            
            await app.disconnect()
            return False
            
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        
        try:
            await app.disconnect()
        except:
            pass
        
        return False
    
    finally:
        print("=" * 70)
        print()


def main():
    """Main entry point."""
    
    print()
    print("Pyrogram Authentication Test")
    print()
    print("Pyrogram is an alternative to Telethon that sometimes")
    print("has better code delivery and fewer issues.")
    print()
    print("Choose test mode:")
    print("1. Quick session check")
    print("2. Full authentication")
    print()
    
    choice = input("Enter choice (1 or 2): ").strip()
    print()
    
    if choice == "1":
        session_valid = asyncio.run(quick_check())
        
        if not session_valid:
            print("Run option 2 for full authentication")
            
    elif choice == "2":
        success = asyncio.run(test_authentication())
        
        if success:
            print()
            print("✅ SUCCESS!")
            print()
            print("Next steps:")
            print("  1. The session is saved in Pyrogram format")
            print("  2. You can use this session with Pyrogram-based apps")
            print("  3. To use with the main app, you may need to convert the session")
        else:
            print()
            print("❌ Authentication failed")
            print()
            print("If code is not arriving:")
            print("  1. Get your own API credentials from https://my.telegram.org")
            print("  2. Update API_ID and API_HASH in this script")
            print("  3. Try again")
    else:
        print("Invalid choice. Please run again and select 1 or 2.")


if __name__ == "__main__":
    main()
