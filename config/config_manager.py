"""
Config Manager for Telegram Mailer MacOS App.

Manages application configuration including:
- API credentials (API_ID and API_HASH)
- Application settings
- Secure storage via MacOS Keychain
"""

import json
import keyring
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from utils.constants import CONFIG_DIR, CONFIG_FILE


class ConfigManager:
    """
    Manages application configuration with secure credential storage.
    
    API_HASH is stored securely in MacOS Keychain via the keyring library.
    Other configuration data is stored in a JSON file.
    """
    
    # Keychain service name for storing API credentials
    KEYCHAIN_SERVICE = "TelegramMailer"
    KEYCHAIN_API_HASH_KEY = "api_hash"
    
    def __init__(self, config_dir: Path = CONFIG_DIR):
        """
        Initialize ConfigManager with configuration directory.
        
        Args:
            config_dir: Directory for storing configuration files
        """
        self.config_dir = config_dir
        self.config_file = config_dir / CONFIG_FILE
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Returns:
            Dict containing configuration data. Returns empty dict if file doesn't exist.
            
        Raises:
            json.JSONDecodeError: If config file contains invalid JSON
        """
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in config file: {self.config_file}",
                e.doc,
                e.pos
            )
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """
        Save configuration to JSON file.
        
        Args:
            config: Dictionary containing configuration data
            
        Note:
            API_HASH should NOT be included in this config dict.
            Use save_api_credentials() for secure credential storage.
        """
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def get_api_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Get API_ID and API_HASH from configuration and Keychain.
        
        Returns:
            Tuple of (api_id, api_hash). Returns (None, None) if not configured.
            
        Note:
            API_ID is stored in config.json
            API_HASH is stored securely in MacOS Keychain
        """
        # Load config to get API_ID
        config = self.load_config()
        api_id = config.get('api_id')
        
        # Get API_HASH from Keychain
        api_hash = None
        if api_id:
            try:
                api_hash = keyring.get_password(
                    self.KEYCHAIN_SERVICE,
                    self.KEYCHAIN_API_HASH_KEY
                )
            except Exception:
                # Keychain access failed, return None
                api_hash = None
        
        return (api_id, api_hash)
    
    def save_api_credentials(self, api_id: str, api_hash: str) -> None:
        """
        Save API_ID and API_HASH with validation.
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            
        Raises:
            ValueError: If credentials fail validation
            
        Note:
            API_ID is stored in config.json
            API_HASH is stored securely in MacOS Keychain
        """
        # Validate credentials
        if not self.validate_credentials(api_id, api_hash):
            raise ValueError("Invalid credentials: API_ID and API_HASH must be non-empty strings")
        
        # Load existing config
        config = self.load_config()
        
        # Save API_ID to config file
        config['api_id'] = api_id
        self.save_config(config)
        
        # Save API_HASH to Keychain
        keyring.set_password(
            self.KEYCHAIN_SERVICE,
            self.KEYCHAIN_API_HASH_KEY,
            api_hash
        )
    
    def validate_credentials(self, api_id: str, api_hash: str) -> bool:
        """
        Validate API credentials.
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            
        Returns:
            True if credentials are valid (non-empty strings after stripping whitespace)
            
        Validation Rules:
            - Both must be strings
            - Both must be non-empty after stripping whitespace
        """
        # Check if both are strings
        if not isinstance(api_id, str) or not isinstance(api_hash, str):
            return False
        
        # Check if both are non-empty after stripping whitespace
        return len(api_id.strip()) > 0 and len(api_hash.strip()) > 0
