#!/usr/bin/env python3
"""
Fix Telegram session database issues.
"""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

# Session file path
SESSION_DIR = Path.home() / "Library" / "Application Support" / "TelegramMailer"
SESSION_FILE = SESSION_DIR / "session_name.session"
BACKUP_DIR = SESSION_DIR / "backups"

def backup_session():
    """Create a backup of the current session."""
    if not SESSION_FILE.exists():
        print("❌ Session file not found")
        return None
    
    # Create backup directory
    BACKUP_DIR.mkdir(exist_ok=True)
    
    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"session_name_{timestamp}.session"
    
    shutil.copy2(SESSION_FILE, backup_file)
    print(f"✓ Backup created: {backup_file}")
    return backup_file

def check_session_integrity():
    """Check if session database is valid."""
    if not SESSION_FILE.exists():
        print("❌ Session file not found")
        return False
    
    try:
        conn = sqlite3.connect(str(SESSION_FILE))
        cursor = conn.cursor()
        
        # Try to read from the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"✓ Database is readable")
        print(f"  Tables found: {[t[0] for t in tables]}")
        
        # Check if we can write
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        
        if result[0] == 'ok':
            print("✓ Database integrity check passed")
        else:
            print(f"❌ Database integrity check failed: {result[0]}")
            conn.close()
            return False
        
        conn.close()
        return True
        
    except sqlite3.OperationalError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def fix_session_permissions():
    """Fix session file permissions."""
    if not SESSION_FILE.exists():
        print("❌ Session file not found")
        return False
    
    import os
    
    # Set permissions to 600 (owner read/write only)
    os.chmod(SESSION_FILE, 0o600)
    print("✓ Permissions set to 600 (owner read/write only)")
    return True

def vacuum_database():
    """Vacuum the database to fix corruption."""
    if not SESSION_FILE.exists():
        print("❌ Session file not found")
        return False
    
    try:
        conn = sqlite3.connect(str(SESSION_FILE))
        conn.execute("VACUUM")
        conn.close()
        print("✓ Database vacuumed successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to vacuum database: {e}")
        return False

def main():
    """Main diagnostic and fix routine."""
    print("=== Telegram Session Diagnostic Tool ===\n")
    
    print(f"Session file: {SESSION_FILE}\n")
    
    # Step 1: Check if file exists
    if not SESSION_FILE.exists():
        print("❌ Session file does not exist")
        print("   You need to authenticate again")
        return
    
    # Step 2: Create backup
    print("📦 Creating backup...")
    backup_file = backup_session()
    if not backup_file:
        return
    print()
    
    # Step 3: Check integrity
    print("🔍 Checking database integrity...")
    is_valid = check_session_integrity()
    print()
    
    if not is_valid:
        print("⚠️  Database appears to be corrupted")
        print("\nOptions:")
        print("1. Try to vacuum the database (may fix minor issues)")
        print("2. Delete session and re-authenticate")
        
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "1":
            print("\n🔧 Attempting to vacuum database...")
            if vacuum_database():
                print("\n✅ Database repaired. Try running the app again.")
            else:
                print("\n❌ Vacuum failed. You may need to delete the session and re-authenticate.")
        elif choice == "2":
            confirm = input("\n⚠️  This will delete your session. Continue? (yes/no): ").strip().lower()
            if confirm == "yes":
                SESSION_FILE.unlink()
                print("✓ Session deleted. Please re-authenticate in the app.")
            else:
                print("Cancelled.")
        else:
            print("Invalid choice.")
    else:
        # Step 4: Fix permissions
        print("🔧 Fixing permissions...")
        fix_session_permissions()
        print()
        
        print("✅ Session appears to be healthy!")
        print("   If you're still having issues, try:")
        print("   1. Restart the application")
        print("   2. Check if another instance is running")
        print("   3. Check system logs for more details")

if __name__ == "__main__":
    main()
