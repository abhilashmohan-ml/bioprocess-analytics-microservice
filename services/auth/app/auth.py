"""Auth-service logic – flat config, bullet-proof."""
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from uuid import uuid4
from typing import Optional, Dict, Any

# shared flat config
from shared.config import settings
from shared.event_bus import event_bus, EventType
from .db import get_user_by_username, create_user_in_db
from .models import RegisterUserRequest, LoginRequest, Token, TokenData

# flat keys
SECRET_KEY = settings.SECRET_KEY
FERNET_KEY = settings.FERNET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Auth-service with flat config."""

    @staticmethod
    def register_user(db, payload: RegisterUserRequest) -> Dict[str, Any]:
        if get_user_by_username(db, payload.username):
            raise ValueError("Username already exists")

        user_data = payload.dict()
        user_data["id"] = uuid4()
        user_data["password_hash"] = pwd_context.hash(payload.password)
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        del user_data["password"]

        user = create_user_in_db(db, user_data)

        event_bus.publish_event(
            EventType.USER_CREATED,
            {
                "user_id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "department": user.department,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return {"user_id": str(user.id), "username": user.username, "message": "User registered successfully"}

    @staticmethod
    def login(db, payload: LoginRequest) -> Optional[Token]:
        user = get_user_by_username(db, payload.username)
        if not user or not pwd_context.verify(payload.password, user.password_hash):
            event_bus.publish_event(
                EventType.USER_LOGIN_FAILED,
                {"username": payload.username, "reason": "user_not_found", "timestamp": datetime.utcnow().isoformat()},
            )
            return None

        if not user.is_active:
            event_bus.publish_event(
                EventType.USER_LOGIN_FAILED,
                {"user_id": str(user.id), "username": user.username, "reason": "inactive_user", "timestamp": datetime.utcnow().isoformat()},
            )
            return None

        # Generate token with flat keys
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token_data = {
            "sub": user.username,
            "id": str(user.id),
            "role": user.role,
            "department": user.department,
            "iat": now,
            "exp": exp,
            "jti": str(uuid4()),
        }

        token = jwt.encode(token_data, SECRET_KEY, ALGORITHM)

        event_bus.publish_event(
            EventType.USER_LOGIN_SUCCESS,
            {
                "user_id": str(user.id),
                "username": user.username,
                "role": user.role,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return Token(access_token=token, token_type="bearer")

    @staticmethod
    def verify_token(token: str) -> TokenData:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            jti = payload.get("jti")
            if jti:
                from shared.config import redis_client
                if redis_client.get(f"revoked_token:{jti}"):
                    raise JWTError("Token has been revoked")

            return TokenData(
                user_id=payload["id"],
                username=payload["sub"],
                role=payload.get("role"),
                department=payload.get("department"),
            )
        except JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")

    @staticmethod
    def revoke_token(token: str) -> bool:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                from shared.config import redis_client
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc).timestamp()
                ttl = int(exp - now)
                if ttl > 0:
                    redis_client.setex(f"revoked_token:{jti}", ttl, "1")
                    return True
            return False
        except JWTError:
            return False