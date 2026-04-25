"""
Encryption utilities for chat messages
Uses Fernet symmetric encryption for at-rest encryption
HIPAA-compliant message encryption
"""
from cryptography.fernet import Fernet
from typing import Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class ChatEncryptionService:
    """
    Service for encrypting/decrypting chat messages
    
    Features:
    - Symmetric encryption using Fernet
    - Automatic encryption/decryption
    - Error handling for corrupted data
    - HIPAA-compliant at-rest encryption
    
    Security:
    - Keys should be stored in environment variables or secrets manager
    - Never log decrypted message content
    - Use separate keys for different environments
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption service
        
        Args:
            encryption_key: Fernet encryption key (32 url-safe base64-encoded bytes)
                          If not provided, uses settings.ENCRYPTION_KEY
        """
        key_str = encryption_key or settings.ENCRYPTION_KEY
        if not key_str:
            logger.warning("ENCRYPTION_KEY not set - encryption will be disabled")
            self._cipher = None
            return
        
        try:
            if isinstance(key_str, str):
                self._key = key_str.encode()
            else:
                self._key = key_str
            self._cipher = Fernet(self._key)
            logger.info("Chat encryption service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise ValueError("Invalid encryption key") from e
    
    def encrypt_message(self, message: str) -> str:
        """
        Encrypt a chat message
        
        Args:
            message: Plain text message to encrypt
            
        Returns:
            Encrypted message (base64-encoded string)
        """
        if not self._cipher:
            # Encryption disabled - return as-is (for development)
            logger.warning("Encryption disabled - message stored in plain text")
            return message
        
        try:
            encrypted_bytes = self._cipher.encrypt(message.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Message encryption failed: {e}")
            raise ValueError("Failed to encrypt message") from e
    
    def decrypt_message(self, encrypted_message: str, is_encrypted: bool = True) -> str:
        """
        Decrypt a chat message
        
        Args:
            encrypted_message: Encrypted message (base64-encoded string) or plain text
            is_encrypted: Whether the message is actually encrypted (default: True)
            
        Returns:
            Decrypted plain text message
        """
        if not self._cipher:
            # Encryption disabled - return as-is (for development)
            return encrypted_message
        
        # If explicitly marked as not encrypted, return as-is
        if not is_encrypted:
            return encrypted_message
        
        try:
            # Try to decrypt - if it fails, it might be plain text with wrong flag
            decrypted_bytes = self._cipher.decrypt(encrypted_message.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            # Check if message looks like plain text (not base64)
            # If decryption fails and message doesn't look encrypted, return as-is
            if self._is_likely_plain_text(encrypted_message):
                logger.warning(f"Message appears to be plain text but marked as encrypted. Returning as-is.")
                return encrypted_message
            
            logger.error(f"Message decryption failed: {e}")
            raise ValueError("Failed to decrypt message") from e
    
    def _is_likely_plain_text(self, message: str) -> bool:
        """
        Check if a message is likely plain text (not encrypted base64)
        Encrypted messages are base64-encoded and have specific characteristics
        """
        if not message:
            return True
        
        # Fernet encrypted messages start with specific prefix and are longer
        # Plain text messages are usually shorter and don't look like base64
        try:
            import base64
            # Check if it's valid base64
            decoded = base64.b64decode(message, validate=True)
            
            # Fernet encrypted messages are typically much longer (at least 100+ chars)
            # and start with specific patterns
            if len(message) < 50:
                # Very short messages are likely plain text
                return True
            
            # Fernet messages start with base64 that decodes to specific structure
            # If it's very short after decoding, it's likely not encrypted
            if len(decoded) < 20:
                return True
            
            # If it's valid base64 and reasonably long, it might be encrypted
            # But decryption will fail if wrong key - we'll handle that in decrypt_message
            return False
        except Exception:
            # Not valid base64 - definitely plain text
            return True
    
    def is_encryption_enabled(self) -> bool:
        """Check if encryption is enabled"""
        return self._cipher is not None
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new Fernet encryption key
        
        Returns:
            Base64-encoded encryption key (as string)
        
        Usage:
            key = ChatEncryptionService.generate_key()
            # Store this key securely in environment variables
        """
        key = Fernet.generate_key()
        return key.decode()


# Global encryption service instance
chat_encryption_service = ChatEncryptionService()


def get_chat_encryption_service() -> ChatEncryptionService:
    """
    Get chat encryption service instance (for dependency injection)
    
    Returns:
        ChatEncryptionService instance
    """
    return chat_encryption_service
