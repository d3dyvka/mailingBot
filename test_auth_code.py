#!/usr/bin/env python3
"""
Test script to check Telegram authentication code sending.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from telegram.telegram_service import TelegramService
from utils.error_logger import ErrorLogger
from utils.constants import ensure_app_directories

async def test_send_code():
    """Test sending authentication code."""
    
    # Ensure directories exist
    ensure_app_directories()
    
    # Initialize error logger
    error_logger = ErrorLogger()
    
    print("=== Telegram Authentication Code Test ===\n")
    
    # Use hardcoded credentials (same as in main app)
    API_ID = "26121943"
    API_HASH = "30e55188d7033e87febc0903c6b48c64"
    
    print(f"✓ API ID: {API_ID}")
    print(f"✓ API Hash: {API_HASH[:10]}...")
    
    # Initialize Telegram service
    telegram_service = TelegramService(
        api_id=API_ID,
        api_hash=API_HASH
    )
    
    # Get phone number
    phone = input("\nEnter phone number (with country code, e.g., +79123456789): ").strip()
    
    if not phone.startswith('+'):
        print("❌ Error: Phone number must start with '+'")
        return
    
    try:
        print("\n📡 Connecting to Telegram...")
        await telegram_service.connect()
        print("✓ Connected successfully")
        
        print(f"\n📤 Sending code request to {phone}...")
        phone_code_hash = await telegram_service.send_code_request(phone)
        
        print(f"✓ Code sent successfully!")
        print(f"✓ Phone code hash: {phone_code_hash[:20]}...")
        print("\n✅ Test PASSED: Code request was sent successfully")
        print("Check your Telegram app or SMS for the code")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {type(e).__name__}")
        print(f"Message: {str(e)}")
        
        # Log the error
        error_logger.log_telegram_error(
            error=e,
            context={
                'phone': phone,
                'test': 'send_code_request'
            }
        )
        
        print(f"\n📝 Error logged to: {error_logger.get_log_path()}")
        
    finally:
        print("\n🔌 Disconnecting...")
        await telegram_service.disconnect()
        print("✓ Disconnected")

if __name__ == "__main__":
    asyncio.run(test_send_code())
