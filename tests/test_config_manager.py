"""
Unit tests for ConfigManager.

Tests configuration management including:
- Loading and saving configuration
- API credentials management
- Validation
- Keychain integration
"""

import json
import pytest
import tempfile
import keyring
from pathlib import Path

from config.config_manager import ConfigManager


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def config_manager(temp_config_dir):
    """Create a ConfigManager instance with temporary directory."""
    return ConfigManager(temp_config_dir)


@pytest.fixture(autouse=True)
def cleanup_keychain():
    """Clean up keychain entries after each test."""
    yield
    # Clean up after test
    try:
        keyring.delete_password(
            ConfigManager.KEYCHAIN_SERVICE,
            ConfigManager.KEYCHAIN_API_HASH_KEY
        )
    except keyring.errors.PasswordDeleteError:
        pass  # Password doesn't exist, that's fine


class TestConfigManagerBasics:
    """Test basic ConfigManager functionality."""
    
    def test_init_creates_directory(self, temp_config_dir):
        """Test that initialization creates config directory."""
        config_dir = temp_config_dir / "new_dir"
        assert not config_dir.exists()
        
        manager = ConfigManager(config_dir)
        assert config_dir.exists()
        assert manager.config_dir == config_dir
    
    def test_load_config_empty_when_no_file(self, config_manager):
        """Test that load_config returns empty dict when file doesn't exist."""
        config = config_manager.load_config()
        assert config == {}
    
    def test_save_and_load_config(self, config_manager):
        """Test saving and loading configuration."""
        test_config = {
            'window_geometry': {'x': 100, 'y': 100, 'width': 800, 'height': 600},
            'last_group_url': 'https://t.me/testgroup',
            'batch_size': 18
        }
        
        config_manager.save_config(test_config)
        loaded_config = config_manager.load_config()
        
        assert loaded_config == test_config
    
    def test_save_config_creates_file(self, config_manager):
        """Test that save_config creates the config file."""
        assert not config_manager.config_file.exists()
        
        config_manager.save_config({'test': 'value'})
        
        assert config_manager.config_file.exists()
    
    def test_load_config_invalid_json(self, config_manager):
        """Test that load_config raises error for invalid JSON."""
        # Write invalid JSON to config file
        with open(config_manager.config_file, 'w') as f:
            f.write("{ invalid json }")
        
        with pytest.raises(json.JSONDecodeError):
            config_manager.load_config()


class TestCredentialValidation:
    """Test credential validation."""
    
    def test_validate_valid_credentials(self, config_manager):
        """Test validation accepts valid credentials."""
        assert config_manager.validate_credentials("123456", "abcdef123456")
    
    def test_validate_rejects_empty_api_id(self, config_manager):
        """Test validation rejects empty API_ID."""
        assert not config_manager.validate_credentials("", "abcdef123456")
    
    def test_validate_rejects_empty_api_hash(self, config_manager):
        """Test validation rejects empty API_HASH."""
        assert not config_manager.validate_credentials("123456", "")
    
    def test_validate_rejects_whitespace_only_api_id(self, config_manager):
        """Test validation rejects whitespace-only API_ID."""
        assert not config_manager.validate_credentials("   ", "abcdef123456")
    
    def test_validate_rejects_whitespace_only_api_hash(self, config_manager):
        """Test validation rejects whitespace-only API_HASH."""
        assert not config_manager.validate_credentials("123456", "   ")
    
    def test_validate_rejects_both_empty(self, config_manager):
        """Test validation rejects both empty."""
        assert not config_manager.validate_credentials("", "")
    
    def test_validate_accepts_credentials_with_surrounding_whitespace(self, config_manager):
        """Test validation accepts credentials with surrounding whitespace."""
        # Validation should pass because strip() removes whitespace
        assert config_manager.validate_credentials("  123456  ", "  abcdef  ")
    
    def test_validate_rejects_non_string_api_id(self, config_manager):
        """Test validation rejects non-string API_ID."""
        assert not config_manager.validate_credentials(123456, "abcdef123456")
    
    def test_validate_rejects_non_string_api_hash(self, config_manager):
        """Test validation rejects non-string API_HASH."""
        assert not config_manager.validate_credentials("123456", 123456)
    
    def test_validate_rejects_none_values(self, config_manager):
        """Test validation rejects None values."""
        assert not config_manager.validate_credentials(None, "abcdef123456")
        assert not config_manager.validate_credentials("123456", None)


class TestAPICredentials:
    """Test API credentials management."""
    
    def test_save_api_credentials(self, config_manager):
        """Test saving API credentials."""
        api_id = "123456"
        api_hash = "abcdef123456"
        
        config_manager.save_api_credentials(api_id, api_hash)
        
        # Check API_ID is in config file
        config = config_manager.load_config()
        assert config['api_id'] == api_id
        
        # Check API_HASH is in Keychain
        stored_hash = keyring.get_password(
            ConfigManager.KEYCHAIN_SERVICE,
            ConfigManager.KEYCHAIN_API_HASH_KEY
        )
        assert stored_hash == api_hash
    
    def test_get_api_credentials(self, config_manager):
        """Test getting API credentials."""
        api_id = "123456"
        api_hash = "abcdef123456"
        
        config_manager.save_api_credentials(api_id, api_hash)
        
        retrieved_id, retrieved_hash = config_manager.get_api_credentials()
        
        assert retrieved_id == api_id
        assert retrieved_hash == api_hash
    
    def test_get_api_credentials_when_not_set(self, config_manager):
        """Test getting credentials when not set returns None."""
        api_id, api_hash = config_manager.get_api_credentials()
        
        assert api_id is None
        assert api_hash is None
    
    def test_save_invalid_credentials_raises_error(self, config_manager):
        """Test that saving invalid credentials raises ValueError."""
        with pytest.raises(ValueError, match="Invalid credentials"):
            config_manager.save_api_credentials("", "abcdef123456")
        
        with pytest.raises(ValueError, match="Invalid credentials"):
            config_manager.save_api_credentials("123456", "")
    
    def test_api_hash_not_in_config_file(self, config_manager):
        """Test that API_HASH is not stored in config file (security)."""
        api_id = "123456"
        api_hash = "abcdef123456"
        
        config_manager.save_api_credentials(api_id, api_hash)
        
        # Read config file directly
        with open(config_manager.config_file, 'r') as f:
            file_content = f.read()
        
        # API_HASH should not be in the file
        assert api_hash not in file_content
        assert 'api_hash' not in file_content.lower()
    
    def test_update_api_credentials(self, config_manager):
        """Test updating existing API credentials."""
        # Save initial credentials
        config_manager.save_api_credentials("123456", "abcdef123456")
        
        # Update credentials
        new_api_id = "789012"
        new_api_hash = "xyz789012"
        config_manager.save_api_credentials(new_api_id, new_api_hash)
        
        # Verify updated credentials
        retrieved_id, retrieved_hash = config_manager.get_api_credentials()
        assert retrieved_id == new_api_id
        assert retrieved_hash == new_api_hash
    
    def test_save_credentials_preserves_other_config(self, config_manager):
        """Test that saving credentials preserves other config values."""
        # Save some config first
        config_manager.save_config({
            'window_geometry': {'x': 100, 'y': 100},
            'batch_size': 18
        })
        
        # Save credentials
        config_manager.save_api_credentials("123456", "abcdef123456")
        
        # Check that other config is preserved
        config = config_manager.load_config()
        assert config['window_geometry'] == {'x': 100, 'y': 100}
        assert config['batch_size'] == 18
        assert config['api_id'] == "123456"


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_config_with_unicode_characters(self, config_manager):
        """Test that config handles Unicode characters correctly."""
        test_config = {
            'last_group_url': 'https://t.me/группа',
            'message': 'Привет! 你好! 🎉'
        }
        
        config_manager.save_config(test_config)
        loaded_config = config_manager.load_config()
        
        assert loaded_config == test_config
    
    def test_config_with_nested_structures(self, config_manager):
        """Test that config handles nested structures."""
        test_config = {
            'window': {
                'geometry': {'x': 100, 'y': 100},
                'state': {'maximized': False}
            },
            'settings': {
                'delays': [15, 20, 25, 30]
            }
        }
        
        config_manager.save_config(test_config)
        loaded_config = config_manager.load_config()
        
        assert loaded_config == test_config
    
    def test_multiple_config_managers_same_directory(self, temp_config_dir):
        """Test that multiple ConfigManager instances can work with same directory."""
        manager1 = ConfigManager(temp_config_dir)
        manager2 = ConfigManager(temp_config_dir)
        
        # Save with manager1
        manager1.save_api_credentials("123456", "abcdef123456")
        
        # Read with manager2
        api_id, api_hash = manager2.get_api_credentials()
        
        assert api_id == "123456"
        assert api_hash == "abcdef123456"
