"""Enhanced authentication service with centralized configuration"""
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from uuid import uuid4
from os import getenv
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

# Import shared configuration
import sys
sys.path.append('../../..')  # Navigate to root
from shared.config import settings
from shared.event_bus import event_bus, EventType
from .models import RegisterUserRequest, LoginRequest, Token, TokenData
from .db import get_user_by_username, create_user_in_db

# Use centralized configuration
SECRET_KEY = settings.security.secret_key
FERNET_KEY = settings.security.fernet_key
ALGORITHM = settings.security.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.security.access_token_expire_minutes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Enhanced authentication service with centralized configuration"""
    
    @staticmethod
    def register_user(db: Session, payload: RegisterUserRequest) -> Dict[str, Any]:
        """Register user with event emission and enhanced validation"""
        
        # Validate input
        if get_user_by_username(db, payload.username):
            raise ValueError("Username already exists")
        
        # Validate password strength
        is_valid, message = settings.security.validate_password_strength(payload.password)
        if not is_valid:
            raise ValueError(message)
        
        # Create user with enhanced security
        user_data = payload.dict()
        user_data["id"] = uuid4()
        user_data["password_hash"] = pwd_context.hash(payload.password)
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        del user_data["password"]
        
        # Store in database
        user = create_user_in_db(db, user_data)
        
        # Emit event for other services
        event_data = {
            "user_id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "department": user.department,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        event_bus.publish_event(EventType.USER_CREATED, event_data)
        
        return {
            "user_id": str(user.id),
            "username": user.username,
            "message": "User registered successfully"
        }
    
    @staticmethod
    def login(db: Session, payload: LoginRequest) -> Optional[Token]:
        """Enhanced login with security features and event tracking"""
        
        user = get_user_by_username(db, payload.username)
        
        if not user:
            # Emit failed login event
            event_bus.publish_event(EventType.USER_LOGIN_FAILED, {
                "username": payload.username,
                "reason": "user_not_found",
                "timestamp": datetime.utcnow().isoformat()
            })
            return None
        
        if not pwd_context.verify(payload.password, user.password_hash):
            # Emit failed login event
            event_bus.publish_event(EventType.USER_LOGIN_FAILED, {
                "user_id": str(user.id),
                "username": user.username,
                "reason": "invalid_password",
                "timestamp": datetime.utcnow().isoformat()
            })
            return None
        
        if not user.is_active:
            event_bus.publish_event(EventType.USER_LOGIN_FAILED, {
                "user_id": str(user.id),
                "username": user.username,
                "reason": "inactive_user",
                "timestamp": datetime.utcnow().isoformat()
            })
            return None
        
        # Generate token with enhanced claims
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        token_data = {
            "sub": user.username,
            "id": str(user.id),
            "role": user.role,
            "department": user.department,
            "iat": now,
            "exp": exp,
            "jti": str(uuid4())  # JWT ID for revocation
        }
        
        token = jwt.encode(token_data, SECRET_KEY, ALGORITHM)
        
        # Emit successful login event
        event_bus.publish_event(EventType.USER_LOGIN_SUCCESS, {
            "user_id": str(user.id),
            "username": user.username,
            "role": user.role,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return Token(access_token=token, token_type="bearer")
    
    @staticmethod
    def verify_token(token: str) -> TokenData:
        """Verify token with revocation check using centralized config"""
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Check if token is revoked (requires Redis)
            jti = payload.get("jti")
            if jti:
                # Import Redis client from shared config
                from shared.config import redis_client
                if redis_client.get(f"revoked_token:{jti}"):
                    raise JWTError("Token has been revoked")
            
            return TokenData(
                user_id=payload["id"],
                username=payload["sub"],
                role=payload.get("role"),
                department=payload.get("department")
            )
            
        except JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    @staticmethod
    def revoke_token(token: str) -> bool:
        """Revoke a token (for logout) using centralized Redis config"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            jti = payload.get("jti")
            exp = payload.get("exp")
            
            if jti and exp:
                # Calculate TTL
                now = datetime.now(timezone.utc).timestamp()
                ttl = int(exp - now)
                
                if ttl > 0:
                    from shared.config import redis_client
                    redis_client.setex(f"revoked_token:{jti}", ttl, "1")
                    return True
            
            return False
            
        except JWTError:
            return False