from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from uuid import uuid4
from os import getenv
from .models import RegisterUserRequest, LoginRequest, Token, TokenData
from .db import get_user_by_username, create_user_in_db

SECRET_KEY = getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    @staticmethod
    def register_user(db, payload):
        if get_user_by_username(db, payload.username):
            raise ValueError("Username exists")
        data = payload.dict()
        data["id"] = uuid4()
        data["password_hash"] = pwd.hash(payload.password)
        del data["password"]
        create_user_in_db(db, data)

    @staticmethod
    def login(db, payload):
        user = get_user_by_username(db, payload.username)
        if user and pwd.verify(payload.password, user.password_hash):
            exp = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            token = jwt.encode({"sub": user.username, "id": str(user.id), "exp": exp}, SECRET_KEY, ALGORITHM)
            return Token(access_token=token, token_type="bearer")
        return None

    @staticmethod
    def verify_token(token: str):
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(user_id=payload["id"])
