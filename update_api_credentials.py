#!/usr/bin/env python3
"""
Automatic script to update API credentials in all files.
"""

import re
from pathlib import Path


def update_credentials_in_file(file_path: Path, api_id: str, api_hash: str) -> bool:
    """Update API credentials in a file."""
    
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern 1: self.API_ID = "..."
        content = re.sub(
            r'self\.API_ID\s*=\s*["\'][\d]+["\']',
            f'self.API_ID = "{api_id}"',
            content
        )
        content = re.sub(
            r'self\.API_HASH\s*=\s*["\'][a-f0-9]+["\']',
            f'self.API_HASH = "{api_hash}"',
            content
        )
        
        # Pattern 2: API_ID = "..."
        content = re.sub(
            r'API_ID\s*=\s*["\'][\d]+["\']',
            f'API_ID = "{api_id}"',
            content
        )
        content = re.sub(
            r'API_HASH\s*=\s*["\'][a-f0-9]+["\']',
            f'API_HASH = "{api_hash}"',
            content
        )
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False


def main():
    """Main entry point."""
    
    print()
    print("=" * 70)
    print("Update API Credentials")
    print("=" * 70)
    print()
    
    print("This script will update API credentials in all project files.")
    print()
    print("First, get your credentials from https://my.telegram.org")
    print()
    
    # Get credentials from user
    print("Enter your API credentials:")
    print()
    
    api_id = input("API_ID (numbers only): ").strip()
    
    if not api_id or not api_id.isdigit():
        print()
        print("❌ Invalid API_ID. Must be numbers only.")
        print("   Example: 12345678")
        return
    
    print()
    api_hash = input("API_HASH (32 characters): ").strip()
    
    if not api_hash or len(api_hash) != 32:
        print()
        print("❌ Invalid API_HASH. Must be exactly 32 characters.")
        print("   Example: abcdef1234567890abcdef1234567890")
        return
    
    print()
    print("Credentials to update:")
    print(f"  API_ID: {api_id}")
    print(f"  API_HASH: {api_hash[:10]}...{api_hash[-10:]}")
    print()
    
    confirm = input("Update all files with these credentials? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print()
        print("Cancelled.")
        return
    
    print()
    print("=" * 70)
    print("Updating files...")
    print("=" * 70)
    print()
    
    # Files to update
    files_to_update = [
        Path('ui/main_window.py'),
        Path('test_auth_code.py'),
        Path('test_full_auth.py'),
        Path('test_auto_auth.py'),
        Path('test_auth_dialog.py'),
        Path('diagnose_telegram_api.py'),
        Path('request_sms_code.py'),
    ]
    
    updated_count = 0
    
    for file_path in files_to_update:
        if update_credentials_in_file(file_path, api_id, api_hash):
            print(f"✓ Updated: {file_path}")
            updated_count += 1
        else:
            print(f"⚠️  Skipped: {file_path}")
    
    print()
    print("=" * 70)
    print(f"Updated {updated_count} files")
    print("=" * 70)
    print()
    
    if updated_count > 0:
        print("✅ Credentials updated successfully!")
        print()
        print("Next steps:")
        print()
        print("1. Rebuild the application:")
        print("   ./build.sh")
        print()
        print("2. Install the new build:")
        print("   cp -R dist/TelegramMailer.app /Applications/")
        print()
        print("3. Test authentication:")
        print("   python3 test_full_auth.py")
        print()
        print("4. The code should now arrive in Telegram! ✅")
    else:
        print("⚠️  No files were updated.")
        print()
        print("Please check:")
        print("  1. Files exist in the project")
        print("  2. Credentials format is correct")
        print("  3. You have write permissions")
    
    print()


if __name__ == "__main__":
    main()
