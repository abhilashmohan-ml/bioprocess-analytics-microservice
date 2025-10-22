"""Security utilities for the bioprocess system"""
import secrets
import string
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Tuple
from cryptography.fernet import Fernet
import os
import logging
import re
from functools import wraps

logger = logging.getLogger(__name__)

class SecurityManager:
    """Centralized security utilities"""
    
    def __init__(self):
        """Initialize security manager with encryption key"""
        self.fernet = Fernet(self._get_or_create_key())
        
    def _get_or_create_key(self) -> bytes:
        """Get or create Fernet encryption key"""
        key = os.getenv("FERNET_KEY")
        if not key:
            key = Fernet.generate_key()
            logger.warning(f"Generated new Fernet key: {key.decode()}")
            logger.warning("Save this key as FERNET_KEY environment variable!")
        return key.encode() if isinstance(key, str) else key
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            return self.fernet.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
            
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
            
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure token"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def hash_data(self, data: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash data with salt using PBKDF2"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        try:
            hashed = hashlib.pbkdf2_hmac(
                'sha256',
                data.encode('utf-8'),
                salt.encode('utf-8'),
                100000  # iterations
            )
            return hashed.hex(), salt
        except Exception as e:
            logger.error(f"Hashing failed: {e}")
            raise
            
    def verify_hash(self, data: str, hashed: str, salt: str) -> bool:
        """Verify data against hash"""
        try:
            new_hash, _ = self.hash_data(data, salt)
            return hmac.compare_digest(new_hash, hashed)
        except Exception as e:
            logger.error(f"Hash verification failed: {e}")
            return False
    
    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit"
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is strong"
    
    def sanitize_input(self, input_string: str) -> str:
        """Sanitize user input"""
        # Remove any potential SQL injection patterns
        sanitized = re.sub(r"[;'\"\\]", "", input_string)
        # Remove any potential XSS patterns
        sanitized = re.sub(r"<[^>]*>", "", sanitized)
        return sanitized.strip()
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_username(self, username: str) -> Tuple[bool, str]:
        """Validate username format"""
        if len(username) < 4 or len(username) > 20:
            return False, "Username must be between 4 and 20 characters"
        
        if not re.match(r"^[a-zA-Z0-9_.-]+$", username):
            return False, "Username can only contain letters, numbers, underscores, dots, and hyphens"
        
        return True, "Username is valid"

# Global security manager instance
security_manager = SecurityManager()

# Security decorators
def require_auth(roles: Optional[list] = None):
    """Decorator to require authentication"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would be implemented with your auth system
            # For now, it's a placeholder
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit(max_calls: int = 100, time_window: int = 60):
    """Rate limiting decorator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would be implemented with Redis
            # For now, it's a placeholder
            return await func(*args, **kwargs)
        return wrapper
    return decorator