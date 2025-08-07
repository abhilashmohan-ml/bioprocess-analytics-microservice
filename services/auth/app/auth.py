from .models import RegisterUserRequest, LoginRequest, Token, TokenData
from .db import get_user_by_username, create_user_in_db
from passlib.context import CryptContext
from datetime import timedelta, datetime, timezone
from jose import jwt, JWTError
from uuid import uuid4
from os import getenv

SECRET_KEY = getenv("SECRET_KEY", "supersecret123")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    @staticmethod
    def register_user(db, payload: RegisterUserRequest):
        if get_user_by_username(db, payload.username):
            raise ValueError("Username already exists")
        # Use an email duplicate check in production.
        data = payload.dict()
        data["id"] = uuid4()
        data["password_hash"] = pwd_context.hash(payload.password)
        del data["password"]
        create_user_in_db(db, data)

    @staticmethod
    def login(db, payload: LoginRequest):
        user = get_user_by_username(db, payload.username)
        # Password check, active status check, approval checks as needed.
        if user and pwd_context.verify(payload.password, user.password_hash):
            exp_time = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = jwt.encode({
                "sub": user.username,
                "id": str(user.id),
                "exp": exp_time
            }, SECRET_KEY, algorithm=ALGORITHM)
            return Token(access_token=access_token, token_type="bearer")
        return None

    @staticmethod
    def verify_token(token: str) -> TokenData:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return TokenData(user_id=payload["id"])
        except JWTError:
            raise ValueError("Token invalid or expired")
