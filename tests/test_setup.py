"""
Tests to verify project setup and structure.
"""

import pytest
from pathlib import Path


def test_project_structure():
    """Verify that all required directories exist."""
    base_dir = Path(__file__).parent.parent
    
    required_dirs = [
        "config",
        "telegram",
        "ui",
        "utils",
        "tests"
    ]
    
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        assert dir_path.exists(), f"Directory {dir_name} does not exist"
        assert dir_path.is_dir(), f"{dir_name} is not a directory"
        
        # Check for __init__.py
        init_file = dir_path / "__init__.py"
        assert init_file.exists(), f"{dir_name}/__init__.py does not exist"


def test_requirements_file():
    """Verify that requirements.txt exists and contains expected dependencies."""
    base_dir = Path(__file__).parent.parent
    requirements_file = base_dir / "requirements.txt"
    
    assert requirements_file.exists(), "requirements.txt does not exist"
    
    content = requirements_file.read_text()
    
    # Check for core dependencies
    required_packages = [
        "telethon",
        "PyQt6",
        "pyinstaller",
        "keyring",
        "hypothesis",
        "pytest"
    ]
    
    for package in required_packages:
        assert package in content, f"Package {package} not found in requirements.txt"


def test_constants_module():
    """Verify that constants module can be imported and has required values."""
    from utils.constants import (
        APP_NAME,
        APP_SUPPORT_DIR,
        DEFAULT_BATCH_SIZE,
        MIN_SAFE_DELAY_HOURS,
        MAX_DELAY_HOURS,
        ensure_app_directories
    )
    
    # Check constants
    assert APP_NAME == "TelegramMailer"
    assert DEFAULT_BATCH_SIZE == 18
    assert MIN_SAFE_DELAY_HOURS == 20
    assert MAX_DELAY_HOURS == 24
    
    # Check that APP_SUPPORT_DIR is a Path object
    assert isinstance(APP_SUPPORT_DIR, Path)
    assert "TelegramMailer" in str(APP_SUPPORT_DIR)
    
    # Check that ensure_app_directories is callable
    assert callable(ensure_app_directories)


def test_app_directories_creation():
    """Verify that ensure_app_directories creates the required directories."""
    from utils.constants import ensure_app_directories, APP_SUPPORT_DIR
    
    # Call the function
    result = ensure_app_directories()
    
    # Verify it returns the app support directory
    assert result == APP_SUPPORT_DIR
    
    # Verify the directory was created
    assert APP_SUPPORT_DIR.exists()
    assert APP_SUPPORT_DIR.is_dir()


def test_module_imports():
    """Verify that all module __init__.py files can be imported."""
    # These imports should not raise any errors
    import config
    import telegram
    import ui
    import utils
    import tests
    
    # Verify modules have expected attributes
    assert hasattr(config, '__file__')
    assert hasattr(telegram, '__file__')
    assert hasattr(ui, '__file__')
    assert hasattr(utils, '__file__')
    
    # Verify __all__ is defined (even if empty for now)
    assert hasattr(config, '__all__')
    assert hasattr(telegram, '__all__')
    assert hasattr(ui, '__all__')
    assert hasattr(utils, '__all__')
