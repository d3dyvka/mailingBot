#!/usr/bin/env python3
"""
Request Telegram code via SMS instead of app.
Sometimes SMS delivery works when app delivery doesn't.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from telethon import TelegramClient
from telethon.tl.functions.auth import SendCodeRequest, ResendCodeRequest
from telethon.errors import PhoneNumberInvalidError, FloodWaitError

# API Credentials
API_ID = "26121943"
API_HASH = "30e55188d7033e87febc0903c6b48c64"
PHONE = "+79137619949"


async def request_sms_code():
    """Request code via SMS."""
    
    print("=" * 70)
    print("Request Telegram Code via SMS")
    print("=" * 70)
    print()
    
    print(f"Phone: {PHONE}")
    print(f"API_ID: {API_ID}")
    print()
    
    client = TelegramClient('sms_test_session', API_ID, API_HASH)
    
    try:
        await client.connect()
        print("✓ Connected to Telegram")
        print()
        
        # First, send regular code request
        print("📤 Sending initial code request...")
        result = await client.send_code_request(PHONE)
        
        print(f"✓ Code request sent")
        print(f"  Phone code hash: {result.phone_code_hash[:30]}...")
        print(f"  Type: {result.type}")
        print()
        
        # Wait a bit
        print("⏱️  Waiting 10 seconds...")
        await asyncio.sleep(10)
        print()
        
        # Try to resend as SMS
        print("📨 Attempting to resend code via SMS...")
        
        try:
            # Use ResendCode to request SMS
            from telethon.tl.functions.auth import ResendCodeRequest
            
            resend_result = await client(ResendCodeRequest(
                phone_number=PHONE,
                phone_code_hash=result.phone_code_hash
            ))
            
            print("✓ SMS code requested!")
            print(f"  Type: {resend_result.type}")
            print()
            print("📱 Check your SMS messages")
            print("   Code should arrive within 1-2 minutes")
            print()
            
            # Save the hash for later use
            print(f"New phone code hash: {resend_result.phone_code_hash}")
            print()
            print("You can use this hash with test_auto_auth.py")
            
        except Exception as e:
            print(f"⚠️  Could not request SMS: {type(e).__name__}")
            print(f"   {str(e)}")
            print()
            print("Telegram may not allow SMS for this API.")
            print()
        
        # Wait for user input
        print()
        code = input("Enter the code when it arrives (or press Enter to skip): ").strip()
        
        if code and len(code) == 5:
            print()
            print(f"🔐 Attempting to sign in with code: {code}")
            
            try:
                await client.sign_in(PHONE, code, phone_code_hash=result.phone_code_hash)
                
                me = await client.get_me()
                print()
                print("✅ SUCCESS! Authenticated!")
                print()
                print(f"User: {me.first_name} {me.last_name or ''}")
                print(f"Phone: {me.phone}")
                print(f"ID: {me.id}")
                print()
                
                # Copy session to app directory
                import shutil
                app_session = Path.home() / "Library" / "Application Support" / "TelegramMailer" / "session_name.session"
                app_session.parent.mkdir(parents=True, exist_ok=True)
                
                if Path('sms_test_session.session').exists():
                    shutil.copy('sms_test_session.session', app_session)
                    print(f"✓ Session copied to: {app_session}")
                    print()
                    print("You can now use the application!")
                
            except Exception as e:
                print(f"❌ Sign in failed: {type(e).__name__}")
                print(f"   {str(e)}")
        
    except FloodWaitError as e:
        print(f"❌ Too many requests!")
        print(f"   Wait {e.seconds} seconds ({e.seconds // 60} minutes)")
        print()
        
    except PhoneNumberInvalidError:
        print("❌ Invalid phone number")
        print()
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}")
        print(f"   {str(e)}")
        print()
        
    finally:
        await client.disconnect()
        
        # Clean up test session
        import os
        if os.path.exists('sms_test_session.session'):
            try:
                os.remove('sms_test_session.session')
            except:
                pass
    
    print()
    print("=" * 70)


async def try_alternative_methods():
    """Try alternative authentication methods."""
    
    print()
    print("=" * 70)
    print("Alternative Authentication Methods")
    print("=" * 70)
    print()
    
    print("If SMS doesn't work, you have these options:")
    print()
    
    print("1. 🔑 Create your own API credentials:")
    print("   - Go to https://my.telegram.org")
    print("   - Log in with your phone number")
    print("   - Create a new application")
    print("   - Use YOUR OWN API_ID and API_HASH")
    print()
    
    print("2. 📱 Use official Telegram app:")
    print("   - Install Telegram Desktop")
    print("   - Log in normally")
    print("   - Then use this app for mailing")
    print()
    
    print("3. 🔄 Try different phone number:")
    print("   - Use a different number")
    print("   - Create API credentials for it")
    print("   - Authorize with that number")
    print()
    
    print("=" * 70)


def main():
    """Main entry point."""
    
    print()
    print("This script will try to request Telegram code via SMS.")
    print()
    print("⚠️  IMPORTANT:")
    print("The main issue is that you're using API credentials that")
    print("don't belong to you. Telegram won't deliver codes reliably.")
    print()
    print("RECOMMENDED: Create your own API credentials at https://my.telegram.org")
    print()
    
    choice = input("Continue anyway? (y/n): ").strip().lower()
    
    if choice != 'y':
        print()
        print("Please create your own API credentials:")
        print("1. Go to https://my.telegram.org")
        print("2. Log in with +79137619949")
        print("3. Go to 'API development tools'")
        print("4. Create new application")
        print("5. Copy API_ID and API_HASH")
        print("6. Update ui/main_window.py lines 65-66")
        print("7. Rebuild: ./build.sh")
        return
    
    print()
    asyncio.run(request_sms_code())
    asyncio.run(try_alternative_methods())


if __name__ == "__main__":
    main()
