"""
Encryption utilities for secure storage of sensitive data
Uses Fernet symmetric encryption (KMS-ready abstraction)
"""

import json
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from loguru import logger

from app.core.config import settings


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data
    
    Features:
    - Symmetric encryption using Fernet
    - JSON serialization support
    - KMS-ready architecture (can be extended to use AWS KMS, GCP KMS, etc.)
    - Secure key handling
    
    Security:
    - Keys should be stored in environment variables or secrets manager
    - Never log decrypted values
    - Use separate keys for different data types if needed
    """
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Initialize encryption service
        
        Args:
            encryption_key: Fernet encryption key (32 url-safe base64-encoded bytes)
                          If not provided, uses settings.ENCRYPTION_KEY
        """
        if encryption_key:
            self._key = encryption_key
        else:
            # Get key from settings
            key_str = settings.ENCRYPTION_KEY
            if isinstance(key_str, str):
                self._key = key_str.encode()
            else:
                self._key = key_str
        
        try:
            self._cipher = Fernet(self._key)
        except Exception as e:
            logger.error("Failed to initialize encryption cipher")
            raise ValueError("Invalid encryption key") from e
    
    def encrypt(self, data: Dict[str, Any]) -> str:
        """
        Encrypt a dictionary to an encrypted string
        
        Args:
            data: Dictionary to encrypt
        
        Returns:
            Encrypted string (base64-encoded)
        
        Raises:
            ValueError: If encryption fails
        """
        try:
            # Convert dict to JSON string
            json_str = json.dumps(data)
            
            # Encrypt
            encrypted_bytes = self._cipher.encrypt(json_str.encode())
            
            # Return as string
            encrypted_str = encrypted_bytes.decode()
            
            logger.debug(f"Successfully encrypted data with {len(data)} fields")
            return encrypted_str
        
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise ValueError("Failed to encrypt data") from e
    
    def decrypt(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt an encrypted string back to a dictionary
        
        Args:
            encrypted_data: Encrypted string (base64-encoded)
        
        Returns:
            Decrypted dictionary
        
        Raises:
            ValueError: If decryption fails
        """
        try:
            # Decrypt
            decrypted_bytes = self._cipher.decrypt(encrypted_data.encode())
            
            # Convert JSON string to dict
            json_str = decrypted_bytes.decode()
            data = json.loads(json_str)
            
            logger.debug(f"Successfully decrypted data with {len(data)} fields")
            return data
        
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise ValueError("Failed to decrypt data") from e
    
    def encrypt_value(self, value: str) -> str:
        """
        Encrypt a single string value
        
        Args:
            value: String to encrypt
        
        Returns:
            Encrypted string (base64-encoded)
        """
        try:
            encrypted_bytes = self._cipher.encrypt(value.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Value encryption failed: {str(e)}")
            raise ValueError("Failed to encrypt value") from e
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """
        Decrypt a single encrypted string value
        
        Args:
            encrypted_value: Encrypted string (base64-encoded)
        
        Returns:
            Decrypted string
        """
        try:
            decrypted_bytes = self._cipher.decrypt(encrypted_value.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Value decryption failed: {str(e)}")
            raise ValueError("Failed to decrypt value") from e
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new Fernet encryption key
        
        Returns:
            Base64-encoded encryption key (as string)
        
        Usage:
            key = EncryptionService.generate_key()
            # Store this key securely in environment variables
        """
        key = Fernet.generate_key()
        return key.decode()
    
    def mask_sensitive_value(self, value: str, visible_chars: int = 4) -> str:
        """
        Mask a sensitive value for logging
        
        Args:
            value: Value to mask
            visible_chars: Number of characters to show at the start
        
        Returns:
            Masked string (e.g., "abc1****")
        """
        if not value:
            return "****"
        
        if len(value) <= visible_chars:
            return "****"
        
        return value[:visible_chars] + "****"
    
    def mask_config(self, config: Dict[str, Any], sensitive_keys: list = None) -> Dict[str, Any]:
        """
        Mask sensitive keys in a configuration dictionary
        
        Args:
            config: Configuration dictionary
            sensitive_keys: List of keys to mask (default: common sensitive keys)
        
        Returns:
            Dictionary with masked sensitive values
        """
        if sensitive_keys is None:
            sensitive_keys = [
                'api_key', 'api_secret', 'password', 'token', 'secret',
                'account_sid', 'auth_token', 'private_key', 'access_token'
            ]
        
        masked_config = config.copy()
        
        for key in sensitive_keys:
            if key in masked_config:
                masked_config[key] = self.mask_sensitive_value(str(masked_config[key]))
        
        return masked_config


# Global encryption service instance
encryption_service = EncryptionService()


def get_encryption_service() -> EncryptionService:
    """
    Get encryption service instance (for dependency injection)
    
    Returns:
        EncryptionService instance
    """
    return encryption_service
