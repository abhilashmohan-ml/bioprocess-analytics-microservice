import re

def validate_email(email: str) -> bool:
    """Check for a basic syntactic email validity."""
    return bool(re.match(r"^[A-Za-z0-9\._%-]+@[A-Za-z0-9\.-]+\.[A-Z|a-z]{2,}$", email))

def validate_username(username: str) -> bool:
    """Check if the username fits expected character rules."""
    return bool(re.match(r"^[a-zA-Z0-9_.-]{4,20}$", username))

def hash_password(pw: str) -> str:
    """Hash using bcrypt (add passlib ctx for prod)."""
    from passlib.context import CryptContext
    ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return ctx.hash(pw)

def verify_password(plain: str, hashed: str) -> bool:
    from passlib.context import CryptContext
    ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return ctx.verify(plain, hashed)
