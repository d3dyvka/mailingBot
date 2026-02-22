#!/usr/bin/env python3
"""
Simple icon generator for Telegram Mailer app
Creates a basic placeholder icon without external dependencies
"""

import os
import subprocess
import sys

def create_simple_icon():
    """Create a simple colored icon using MacOS built-in tools"""
    
    resources_dir = "resources"
    os.makedirs(resources_dir, exist_ok=True)
    
    # Create a simple 512x512 PNG with a solid color
    # We'll use Python to create a minimal PNG
    
    # Simple approach: Create a minimal valid PNG file
    # This is a 1x1 blue pixel PNG that we'll scale up
    png_data = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x02, 0x00,  # 512x512 dimensions
        0x08, 0x02, 0x00, 0x00, 0x00, 0xF4, 0x7F, 0xB6,
        0xC1,
    ])
    
    # For simplicity, let's just create a note that icon is missing
    # and let PyInstaller use default icon
    
    readme_path = os.path.join(resources_dir, "ICON_PLACEHOLDER.txt")
    with open(readme_path, 'w') as f:
        f.write("""
Icon Placeholder
================

No custom icon has been created yet.

To add a custom icon:
1. Create or obtain a 1024x1024 PNG image
2. Use online tools to convert to .icns:
   - https://cloudconvert.com/png-to-icns
   - https://iconverticons.com/online/
3. Save as resources/icon.icns

The app will build successfully without a custom icon,
using PyInstaller's default icon instead.
""")
    
    print("✓ Icon placeholder created")
    print("⚠ No custom icon available - app will use default icon")
    print(f"  See {readme_path} for instructions")
    
    return False  # No icon created

if __name__ == "__main__":
    create_simple_icon()
