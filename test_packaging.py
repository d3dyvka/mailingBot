#!/usr/bin/env python3
"""
Test script to verify packaging configuration
Checks that all required components are present before building
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version is 3.11+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"❌ Python version {version.major}.{version.minor} is too old")
        print("   Required: Python 3.11+")
        return False
    print(f"✅ Python version {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check that all required dependencies are installed"""
    required = [
        'telethon',
        'PyQt6',
        'PyInstaller',
        'keyring',
        'hypothesis',
        'pytest',
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} not installed")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Install missing packages: pip3 install {' '.join(missing)}")
        return False
    return True

def check_files():
    """Check that all required files exist"""
    required_files = [
        'telegram_mailer.spec',
        'build.sh',
        'main.py',
        'requirements.txt',
        'resources/Info.plist',
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def check_icon():
    """Check if icon exists"""
    icon_path = 'resources/icon.icns'
    if os.path.exists(icon_path):
        print(f"✅ {icon_path} exists")
        return True
    else:
        print(f"⚠️  {icon_path} not found (will use default icon)")
        return True  # Not critical

def check_modules():
    """Check that all application modules exist"""
    modules = [
        'config/config_manager.py',
        'telegram/telegram_service.py',
        'telegram/mailing_service.py',
        'ui/main_window.py',
        'ui/text_editor_panel.py',
        'ui/progress_panel.py',
        'utils/progress_tracker.py',
        'utils/delay_calculator.py',
        'utils/error_logger.py',
        'utils/power_manager.py',
    ]
    
    all_exist = True
    for module in modules:
        if os.path.exists(module):
            print(f"✅ {module} exists")
        else:
            print(f"❌ {module} missing")
            all_exist = False
    
    return all_exist

def check_macos():
    """Check if running on MacOS"""
    if sys.platform != 'darwin':
        print(f"❌ Not running on MacOS (detected: {sys.platform})")
        print("   MacOS is required to build .app bundles")
        return False
    print("✅ Running on MacOS")
    return True

def check_build_tools():
    """Check if required build tools are available"""
    tools = {
        'iconutil': 'MacOS icon utility',
        'codesign': 'Code signing tool',
        'security': 'Keychain access tool',
    }
    
    all_available = True
    for tool, description in tools.items():
        try:
            subprocess.run([tool, '--version'], 
                         capture_output=True, 
                         check=False)
            print(f"✅ {tool} available ({description})")
        except FileNotFoundError:
            print(f"⚠️  {tool} not found ({description})")
            # Not critical for basic build
    
    return True  # Not critical

def main():
    """Run all checks"""
    print("=" * 60)
    print("Telegram Mailer - Packaging Configuration Test")
    print("=" * 60)
    print()
    
    checks = [
        ("MacOS Platform", check_macos),
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Required Files", check_files),
        ("Application Modules", check_modules),
        ("Icon File", check_icon),
        ("Build Tools", check_build_tools),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n--- {name} ---")
        result = check_func()
        results.append((name, result))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
        if not result:
            all_passed = False
    
    print()
    if all_passed:
        print("✅ All checks passed! Ready to build.")
        print("\nRun: ./build.sh")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
