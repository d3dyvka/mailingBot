#!/usr/bin/env python3
"""
Simple Pyrogram authentication test.
"""

import asyncio
import sys

# Fix for Python 3.14 event loop issue with Pyrogram
if sys.version_info >= (3, 10):
    import asyncio
    import threading
    
    # Create and set event loop before importing Pyrogram
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import Client

# API Credentials
api_id = 26121943
api_hash = "30e55188d7033e87febc0903c6b48c64"
phone = "+79137619949"

print()
print("=" * 70)
print("Simple Pyrogram Authentication")
print("=" * 70)
print()
print(f"API_ID: {api_id}")
print(f"API_HASH: {api_hash[:15]}...")
print(f"Phone: {phone}")
print()

# Create client
app = Client(
    "my_account",
    api_id=api_id,
    api_hash=api_hash
)

print("Starting authentication...")
print()

# Start the client (this will handle auth automatically)
with app:
    me = app.get_me()
    
    print("✅ SUCCESS! Authenticated!")
    print()
    print(f"Name: {me.first_name} {me.last_name or ''}")
    print(f"Phone: {me.phone_number}")
    print(f"Username: @{me.username}" if me.username else "Username: (not set)")
    print(f"ID: {me.id}")
    print()
    print("Session saved as: my_account.session")
    print()

print("=" * 70)
