"""
AES-256 Encryption Module for PII Protection (DPDP Compliance)

This module provides AES-256-CBC encryption for Personally Identifiable Information (PII)
as required by India's DPDP (Digital Personal Data Protection) Act.

Key Strategy:
- Names: Only encrypted (no search needed)
- Emails: Both encrypted + hashed for login/search
- Passwords: Bcrypt hashed (never encrypted)
"""

import hashlib
import hmac
import secrets
from base64 import b64encode, b64decode
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from config.settings import get_settings
import logging

logger = logging.getLogger(__name__)


class AES256Encryptor:
    """
    AES-256-CBC Encryption handler for PII protection
    Uses random IV for each encryption to prevent pattern analysis
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._validate_keys()
    
    def _validate_keys(self):
        """Validate that encryption keys are properly configured"""
        if not self.settings.AES_KEY:
            raise ValueError("AES_KEY environment variable is not configured")
        
        # Decode base64 keys
        try:
            self.key = b64decode(self.settings.AES_KEY)
            if len(self.key) != 32:  # 256 bits = 32 bytes
                raise ValueError(f"AES_KEY must decode to 32 bytes (256 bits), got {len(self.key)}")
        except Exception as e:
            raise ValueError(f"Invalid AES_KEY encoding: {str(e)}")
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext using AES-256-CBC
        
        Returns: base64 encoded string in format "iv:ciphertext"
        Each encryption generates a random IV to prevent pattern analysis
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            str: base64 encoded "iv:ciphertext"
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty plaintext")
        
        # Generate random IV (16 bytes for AES)
        iv = secrets.token_bytes(16)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Add PKCS7 padding
        plaintext_bytes = plaintext.encode("utf-8")
        padded = self._pkcs7_pad(plaintext_bytes)
        
        # Encrypt
        ciphertext = encryptor.update(padded) + encryptor.finalize()
        
        # Return base64 encoded IV:ciphertext
        iv_b64 = b64encode(iv).decode("utf-8")
        ciphertext_b64 = b64encode(ciphertext).decode("utf-8")
        
        return f"{iv_b64}:{ciphertext_b64}"
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt AES-256-CBC encrypted data
        
        Args:
            encrypted_data: String in format "iv:ciphertext" (base64 encoded)
            
        Returns:
            str: Decrypted plaintext
        """
        if not encrypted_data:
            raise ValueError("Cannot decrypt empty data")
        
        try:
            # Split IV and ciphertext
            iv_b64, ciphertext_b64 = encrypted_data.split(":", 1)
            iv = b64decode(iv_b64)
            ciphertext = b64decode(ciphertext_b64)
            
            if len(iv) != 16:
                raise ValueError("Invalid IV length")
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Remove PKCS7 padding
            plaintext = self._pkcs7_unpad(padded_plaintext)
            
            return plaintext.decode("utf-8")
        
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise ValueError(f"Failed to decrypt data: {str(e)}")
    
    @staticmethod
    def _pkcs7_pad(data: bytes) -> bytes:
        """Apply PKCS7 padding"""
        block_size = 16
        pad_length = block_size - (len(data) % block_size)
        padding = bytes([pad_length] * pad_length)
        return data + padding
    
    @staticmethod
    def _pkcs7_unpad(data: bytes) -> bytes:
        """Remove PKCS7 padding"""
        pad_length = data[-1]
        return data[:-pad_length]


class EmailHasher:
    """
    Email hashing for searchable/unique identification.
    Uses SHA-256 with HMAC for additional security.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.secret = self.settings.SECRET_KEY.encode()
    
    def hash_email(self, email: str) -> str:
        """
        Hash email for unique identification and searches
        Using HMAC-SHA256 for additional security
        
        Args:
            email: Email address to hash
            
        Returns:
            str: Hex-encoded hash
        """
        email_lower = email.lower().strip()
        hash_obj = hmac.new(
            self.secret,
            email_lower.encode("utf-8"),
            hashlib.sha256
        )
        return hash_obj.hexdigest()
    
    def verify_email_hash(self, email: str, email_hash: str) -> bool:
        """
        Verify if email matches the hash
        
        Args:
            email: Email to verify
            email_hash: Hash to compare against
            
        Returns:
            bool: True if email matches hash
        """
        computed_hash = self.hash_email(email)
        return hmac.compare_digest(computed_hash, email_hash)


# Global instances
_encryptor = None
_email_hasher = None


def get_encryptor() -> AES256Encryptor:
    """Get or create global encryptor instance"""
    global _encryptor
    if _encryptor is None:
        _encryptor = AES256Encryptor()
    return _encryptor


def get_email_hasher() -> EmailHasher:
    """Get or create global email hasher instance"""
    global _email_hasher
    if _email_hasher is None:
        _email_hasher = EmailHasher()
    return _email_hasher


# Convenience functions
def encrypt_pii(plaintext: str) -> str:
    """Encrypt PII data"""
    return get_encryptor().encrypt(plaintext)


def decrypt_pii(encrypted_data: str) -> str:
    """Decrypt PII data"""
    return get_encryptor().decrypt(encrypted_data)


def hash_email(email: str) -> str:
    """Hash email for searches"""
    return get_email_hasher().hash_email(email)


def verify_email_hash(email: str, email_hash: str) -> bool:
    """Verify email against hash"""
    return get_email_hasher().verify_email_hash(email, email_hash)
