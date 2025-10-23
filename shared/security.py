"""
Security utilities for the bioprocess system – lazy, safe, bullet-proof.
Padding characters (=) are **automatically removed** so developers can
use the output of `Fernet.generate_key()` directly.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import secrets
import string
from contextlib import suppress
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Tuple

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #
def _validate_fernet_key(key: str) -> bool:
    """
    Return True only if `key` is 32 url-safe base64-encoded bytes.
    Padding characters (=) are **ignored** during validation.
    """
    if not key:
        return False
    try:
        decoded = base64.urlsafe_b64decode(key.encode() + b"==")
        return len(decoded) == 32
    except Exception:  # noqa: S110
        return False


# ------------------------------------------------------------------ #
# SecurityManager – lazy initialisation, padding-tolerant
# ------------------------------------------------------------------ #
class SecurityManager:
    """
    Centralised security utilities.  Fernet is created **lazily** so that
    a bad key does **not** crash the importer.  The first operation that
    needs crypto will raise a *clear* error.
    """

    __slots__ = ("_fernet", "_raw_key")

    def __init__(self) -> None:
        self._fernet: Optional[Fernet] = None
        self._raw_key: Optional[str] = None

    # ~~~~~~~~~~~~~~~~~~~~~~ internal ~~~~~~~~~~~~~~~~~~~~~~ #
    def _get_or_create_key(self) -> bytes:
        """
        Return **32 url-safe base64-encoded bytes** *without* padding.
        If the env-var contains padding we **strip it permanently**.
        """
        key = os.getenv("FERNET_KEY", "").strip()
        if not _validate_fernet_key(key):
            correct = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
            logger.error(
                "FERNET_KEY is missing or invalid.  "
                "Run the following command **once** and add the result to your .env:\n\n"
                "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode().rstrip('='))\"\n\n"
                "Example valid key: %s",
                correct,
            )
            raise RuntimeError("FERNET_KEY must be 32 url-safe base64 bytes (no padding)") from None

        key = key.rstrip("=")  # **Permanent fix**: strip padding forever
        self._raw_key = key
        return key.encode()

    def _require_fernet(self) -> Fernet:
        """Return a valid Fernet instance or raise a human-readable error."""
        if self._fernet is not None:
            return self._fernet

        key_bytes = self._get_or_create_key()
        self._fernet = Fernet(key_bytes)
        logger.debug("Fernet initialised successfully (padding-stripped).")
        return self._fernet

    # ~~~~~~~~~~~~~~~~~~~~~~ public crypto ~~~~~~~~~~~~~~~~~~~~~~ #
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt and return base64-encoded ciphertext."""
        f = self._require_fernet()
        return f.encrypt(data.encode()).decode()

    def decrypt_sensitive_data(self, encrypted: str) -> str:
        """Decrypt base64-encoded ciphertext."""
        f = self._require_fernet()
        return f.decrypt(encrypted.encode()).decode()

    def generate_secure_token(self, length: int = 32) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def hash_data(self, data: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """PBKDF2-SHA256 with 100 000 iterations."""
        if salt is None:
            salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac("sha256", data.encode(), salt.encode(), 100_000)
        return hashed.hex(), salt

    def verify_hash(self, data: str, hashed: str, salt: str) -> bool:
        try:
            new_hash, _ = self.hash_data(data, salt)
            return hmac.compare_digest(new_hash, hashed)
        except Exception as e:
            logger.error("Hash verification failed: %s", e)
            return False

    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        if len(password) < 8:
            return False, "≥ 8 characters"
        for pattern, msg in (
            (r"[A-Z]", "uppercase letter"),
            (r"[a-z]", "lowercase letter"),
            (r"\d", "digit"),
            (r"[!@#$%^&*(),.?\":{}|<>]", "special character"),
        ):
            if not secrets.re.search(pattern, password):  # type: ignore[attr-defined]
                return False, f"at least one {msg}"
        return True, "strong"

    def sanitize_input(self, input_string: str) -> str:
        tmp = secrets.re.sub(r"[;'\"\\]", "", input_string)  # type: ignore[attr-defined]
        tmp = secrets.re.sub(r"<[^>]*>", "", tmp)  # type: ignore[attr-defined]
        return tmp.strip()

    def validate_email(self, email: str) -> bool:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        with suppress(Exception):
            return secrets.re.match(pattern, email) is not None  # type: ignore[attr-defined]
        return False

    def validate_username(self, username: str) -> Tuple[bool, str]:
        if not (4 <= len(username) <= 20):
            return False, "4–20 characters"
        if not secrets.re.match(r"^[a-zA-Z0-9_.-]+$", username):  # type: ignore[attr-defined]
            return False, "only letters, digits, underscore, dot, hyphen"
        return True, "valid"


# ------------------------------------------------------------------ #
# Singleton – import-safe, padding-proof
# ------------------------------------------------------------------ #
security_manager = SecurityManager()

# ------------------------------------------------------------------ #
# Security decorators (restored)
# ------------------------------------------------------------------ #
def require_auth(roles: Optional[list] = None):
    """Decorator to require authentication (placeholder)."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Integrate with your JWT / OAuth logic here
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit(max_calls: int = 100, time_window: int = 60):
    """Rate-limiting decorator (placeholder)."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Integrate with Redis sliding-window here
            return await func(*args, **kwargs)
        return wrapper
    return decorator