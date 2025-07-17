import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""
    
    def __init__(self):
        self._fernet = None
        self._initialize_key()
    
    def _initialize_key(self):
        """Initialize encryption key from environment or generate if needed."""
        # Try to get key from environment
        key = os.getenv("FILE_ORBIT_ENCRYPTION_KEY")
        
        if not key:
            # Generate key from a passphrase if no key is set
            passphrase = os.getenv("FILE_ORBIT_ENCRYPTION_PASSPHRASE", "file-orbit-default-passphrase")
            salt = os.getenv("FILE_ORBIT_ENCRYPTION_SALT", "file-orbit-salt").encode()
            
            # Use PBKDF2 to derive a key from the passphrase
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
        else:
            key = key.encode() if isinstance(key, str) else key
        
        self._fernet = Fernet(key)
    
    def encrypt(self, value: str) -> str:
        """Encrypt a string value."""
        if not value:
            return value
        
        encrypted = self._fernet.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_value: str) -> str:
        """Decrypt an encrypted string value."""
        if not encrypted_value:
            return encrypted_value
        
        try:
            decoded = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted = self._fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            # If decryption fails, assume it's not encrypted and return as-is
            # This helps with backward compatibility
            return encrypted_value
    
    def is_encrypted(self, value: str) -> bool:
        """Check if a value appears to be encrypted."""
        if not value:
            return False
        
        try:
            # Try to decode as base64 and decrypt
            decoded = base64.urlsafe_b64decode(value.encode())
            self._fernet.decrypt(decoded)
            return True
        except Exception:
            return False


# Global instance
encryption_service = EncryptionService()


# List of setting keys that should be encrypted
ENCRYPTED_SETTINGS = {
    "email.smtp_password",
    "aws.secret_access_key",
    "monitoring.datadog_api_key",
    "security.ldap_bind_password",
    # Add more sensitive settings here as needed
}


def should_encrypt_setting(key: str) -> bool:
    """Check if a setting should be encrypted based on its key."""
    return key in ENCRYPTED_SETTINGS