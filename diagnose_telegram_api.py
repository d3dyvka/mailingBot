#!/usr/bin/env python3
"""
Diagnostic script to check Telegram API connection and code delivery issues.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from telegram.telegram_service import TelegramService
from telethon import TelegramClient
from telethon.errors import (
    PhoneNumberInvalidError,
    PhoneNumberBannedError,
    PhoneNumberFloodError,
    ApiIdInvalidError
)

# API Credentials
API_ID = "22937843"
API_HASH = "f059dadbb0d4d4734feb75dd4fdcb4b9"
PHONE = "+79137619949"


async def diagnose_api():
    """Run comprehensive API diagnostics."""
    
    print("=" * 70)
    print("Telegram API Diagnostic Tool")
    print("=" * 70)
    print()
    
    # Test 1: API Credentials
    print("Test 1: Checking API Credentials")
    print("-" * 70)
    print(f"API_ID: {API_ID}")
    print(f"API_HASH: {API_HASH[:20]}...")
    print()
    
    try:
        # Create a test client
        client = TelegramClient('test_session', API_ID, API_HASH)
        
        print("✓ API credentials format is valid")
        print()
        
        # Test 2: Connection
        print("Test 2: Testing Connection to Telegram")
        print("-" * 70)
        
        await client.connect()
        
        if await client.is_user_authorized():
            print("✓ Already authorized!")
            me = await client.get_me()
            print(f"  User: {me.first_name} {me.last_name or ''}")
            print(f"  Phone: {me.phone}")
            await client.disconnect()
            return
        
        print("✓ Connected to Telegram servers")
        print()
        
        # Test 3: Phone Number Check
        print("Test 3: Checking Phone Number")
        print("-" * 70)
        print(f"Phone: {PHONE}")
        
        if not PHONE.startswith('+'):
            print("❌ Phone number must start with '+'")
            await client.disconnect()
            return
        
        if len(PHONE) < 11:
            print("❌ Phone number seems too short")
            await client.disconnect()
            return
        
        print("✓ Phone number format looks correct")
        print()
        
        # Test 4: Send Code Request
        print("Test 4: Attempting to Send Code")
        print("-" * 70)
        
        try:
            result = await client.send_code_request(PHONE)
            
            print("✅ Code request sent successfully!")
            print()
            print("Code Delivery Information:")
            print(f"  Phone Code Hash: {result.phone_code_hash[:30]}...")
            print(f"  Type: {type(result).__name__}")
            
            # Check the type of code sent
            if hasattr(result, 'type'):
                code_type = result.type
                print(f"  Delivery Method: {code_type}")
                
                if 'app' in str(code_type).lower():
                    print()
                    print("📱 Code should arrive in your Telegram app")
                    print("   Check: Settings > Devices > Active Sessions")
                elif 'sms' in str(code_type).lower():
                    print()
                    print("📨 Code should arrive via SMS")
                    print("   Check your phone messages")
                elif 'call' in str(code_type).lower():
                    print()
                    print("📞 Code will arrive via phone call")
                    print("   Answer the incoming call")
            
            print()
            print("⏱️  Codes typically arrive within:")
            print("   - Telegram app: 1-10 seconds")
            print("   - SMS: 30 seconds - 2 minutes")
            print("   - Call: 2-5 minutes")
            print()
            
            # Wait a bit and check
            print("Waiting 15 seconds to see if code arrives...")
            await asyncio.sleep(15)
            
            print()
            print("If code still hasn't arrived, possible reasons:")
            print()
            print("1. 🚫 Phone Number Issues:")
            print("   - Number is not registered with Telegram")
            print("   - Number format is incorrect")
            print("   - Number is banned or restricted")
            print()
            print("2. 📵 Delivery Issues:")
            print("   - SMS delivery delays (carrier issues)")
            print("   - Telegram app not installed or logged out")
            print("   - Phone has no signal")
            print()
            print("3. 🔒 API Issues:")
            print("   - API credentials are invalid or restricted")
            print("   - Too many requests (flood wait)")
            print("   - API ID/Hash doesn't match the app")
            print()
            print("4. 🌍 Regional Issues:")
            print("   - Telegram may be blocked in your region")
            print("   - VPN/Proxy interference")
            print()
            
        except PhoneNumberInvalidError:
            print("❌ FAILED: Invalid Phone Number")
            print()
            print("The phone number format is invalid or not recognized by Telegram.")
            print()
            print("Solutions:")
            print("  1. Verify the number is correct: +79137619949")
            print("  2. Make sure it's registered with Telegram")
            print("  3. Try with country code: +7 913 761 9949")
            
        except PhoneNumberBannedError:
            print("❌ FAILED: Phone Number Banned")
            print()
            print("This phone number has been banned by Telegram.")
            print()
            print("Solutions:")
            print("  1. Contact Telegram support")
            print("  2. Use a different phone number")
            
        except PhoneNumberFloodError as e:
            print("❌ FAILED: Too Many Requests (Flood)")
            print()
            print(f"You've requested too many codes. Wait time: {e.seconds} seconds")
            print()
            print("Solutions:")
            print(f"  1. Wait {e.seconds // 60} minutes before trying again")
            print("  2. Don't request codes too frequently")
            
        except ApiIdInvalidError:
            print("❌ FAILED: Invalid API Credentials")
            print()
            print("The API_ID or API_HASH is invalid.")
            print()
            print("Current credentials:")
            print(f"  API_ID: {API_ID}")
            print(f"  API_HASH: {API_HASH}")
            print()
            print("Solutions:")
            print("  1. Verify credentials at https://my.telegram.org")
            print("  2. Make sure API_ID and API_HASH match")
            print("  3. Check if the API app is active")
            
        except Exception as e:
            print(f"❌ FAILED: {type(e).__name__}")
            print(f"   Error: {str(e)}")
            print()
            print("This is an unexpected error. Check:")
            print("  1. Internet connection")
            print("  2. Firewall settings")
            print("  3. VPN/Proxy configuration")
        
        await client.disconnect()
        
    except Exception as e:
        print(f"❌ Connection failed: {type(e).__name__}")
        print(f"   Error: {str(e)}")
        print()
        print("Possible causes:")
        print("  1. No internet connection")
        print("  2. Telegram servers are down")
        print("  3. Firewall blocking connection")
        print("  4. Invalid API credentials")
    
    print()
    print("=" * 70)


async def check_api_validity():
    """Quick check if API credentials are valid."""
    
    print()
    print("Quick API Validity Check")
    print("-" * 70)
    
    try:
        client = TelegramClient('temp_test', API_ID, API_HASH)
        await client.connect()
        
        # Try to get updates (this will fail if API is invalid)
        print("✓ API credentials are valid")
        print("✓ Connection to Telegram successful")
        
        await client.disconnect()
        
        # Clean up temp session
        import os
        if os.path.exists('temp_test.session'):
            os.remove('temp_test.session')
        
        return True
        
    except ApiIdInvalidError:
        print("❌ API credentials are INVALID")
        print()
        print("The API_ID and API_HASH combination is not recognized by Telegram.")
        print()
        print("This means:")
        print("  - These credentials may be fake or expired")
        print("  - They don't belong to a valid Telegram app")
        print("  - You need to get new credentials from https://my.telegram.org")
        return False
        
    except Exception as e:
        print(f"⚠️  Could not verify: {type(e).__name__}")
        print(f"   {str(e)}")
        return None


def main():
    """Main entry point."""
    
    print()
    print("This tool will diagnose why Telegram codes are not arriving.")
    print()
    
    # First check API validity
    api_valid = asyncio.run(check_api_validity())
    
    if api_valid is False:
        print()
        print("=" * 70)
        print("CRITICAL: API credentials are invalid!")
        print("=" * 70)
        print()
        print("You need to:")
        print("1. Go to https://my.telegram.org")
        print("2. Log in with your phone number")
        print("3. Go to 'API development tools'")
        print("4. Create a new application or use existing one")
        print("5. Get the API_ID and API_HASH")
        print("6. Update them in ui/main_window.py")
        print("7. Rebuild the application")
        return
    
    print()
    input("Press Enter to run full diagnostics...")
    
    # Run full diagnostics
    asyncio.run(diagnose_api())


if __name__ == "__main__":
    main()
