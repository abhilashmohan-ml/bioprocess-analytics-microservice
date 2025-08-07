from .db import User, Base
from .models import UserCreate, UserRead
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from uuid import uuid4

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    @staticmethod
    def create_user(db: Session, payload: UserCreate) -> UserRead:
        user = User(
            id=uuid4(),
            username=payload.username,
            email=payload.email,
            first_name=payload.first_name,
            last_name=payload.last_name,
            password_hash=pwd_context.hash(payload.password),
            role=payload.role,
            department=payload.department,
            phone_number=payload.phone_number,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return UserRead(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            department=user.department,
            phone_number=user.phone_number,
            is_active=user.is_active,
        )

    @staticmethod
    def get_user(db: Session, user_id: str) -> UserRead:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        return UserRead(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            department=user.department,
            phone_number=user.phone_number,
            is_active=user.is_active,
        )
