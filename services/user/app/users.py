"""User service logic with centralized configuration"""
from .db import User, Base
from .models import UserCreate, UserRead
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import Optional 
from uuid import uuid4
import logging
import sys

# Import centralized configuration
sys.path.append('../../..')
from shared.config import settings
from shared.security import security_manager

logger = logging.getLogger(__name__)

# Use centralized bcrypt configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    """User service with centralized configuration and security"""
    
    @staticmethod
    def create_user(db: Session, payload: UserCreate) -> UserRead:
        """Create user with centralized validation and security"""
        
        # Validate username using centralized validation
        is_valid, message = security_manager.validate_username(payload.username)
        if not is_valid:
            raise ValueError(message)
        
        # Validate email using centralized validation
        if not security_manager.validate_email(payload.email):
            raise ValueError("Invalid email format")
        
        # Validate password strength using centralized validation
        is_valid, message = security_manager.validate_password_strength(payload.password)
        if not is_valid:
            raise ValueError(message)
        
        # Sanitize input using centralized sanitizer
        sanitized_data = {
            "username": security_manager.sanitize_input(payload.username),
            "email": security_manager.sanitize_input(payload.email),
            "first_name": security_manager.sanitize_input(payload.first_name) if payload.first_name else None,
            "last_name": security_manager.sanitize_input(payload.last_name) if payload.last_name else None,
            "role": security_manager.sanitize_input(payload.role),
            "department": security_manager.sanitize_input(payload.department) if payload.department else None,
            "phone_number": security_manager.sanitize_input(payload.phone_number) if payload.phone_number else None,
        }
        
        # Create user with centralized security
        user = User(
            id=uuid4(),
            username=sanitized_data["username"],
            email=sanitized_data["email"],
            first_name=sanitized_data["first_name"],
            last_name=sanitized_data["last_name"],
            password_hash=pwd_context.hash(payload.password),
            role=sanitized_data["role"],
            department=sanitized_data["department"],
            phone_number=sanitized_data["phone_number"],
            is_active=True,
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"✅ User created successfully: {user.username} (ID: {user.id})")
        
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
    def get_user(db: Session, user_id: str) -> Optional[UserRead]:
        """Get user by ID with centralized logging"""
        logger.debug(f"Looking up user by ID: {user_id}")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            logger.warning(f"User not found: {user_id}")
            return None
        
        logger.debug(f"User found: {user.username} (ID: {user.id})")
        
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
    def update_user(db: Session, user_id: str, updates: dict) -> Optional[UserRead]:
        """Update user with centralized validation"""
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            logger.warning(f"Update failed - user not found: {user_id}")
            return None
        
        # Validate updates
        if 'username' in updates:
            is_valid, message = security_manager.validate_username(updates['username'])
            if not is_valid:
                raise ValueError(message)
            updates['username'] = security_manager.sanitize_input(updates['username'])
        
        if 'email' in updates:
            if not security_manager.validate_email(updates['email']):
                raise ValueError("Invalid email format")
            updates['email'] = security_manager.sanitize_input(updates['email'])
        
        # Sanitize all string updates
        for key, value in updates.items():
            if isinstance(value, str):
                updates[key] = security_manager.sanitize_input(value)
        
        # Apply updates
        for key, value in updates.items():
            setattr(user, key, value)
        
        user.updated_at = __import__('datetime').datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        logger.info(f"✅ User updated successfully: {user.username} (ID: {user.id})")
        
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
    def delete_user(db: Session, user_id: str) -> bool:
        """Soft delete user (deactivate)"""
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            logger.warning(f"Delete failed - user not found: {user_id}")
            return False
        
        user.is_active = False
        user.updated_at = __import__('datetime').datetime.utcnow()
        db.commit()
        
        logger.info(f"✅ User deactivated: {user.username} (ID: {user.id})")
        return True

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username for authentication"""
        logger.debug(f"Looking up user by username: {username}")
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        logger.debug(f"Looking up user by email: {email}")
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def list_users(db: Session, skip: int = 0, limit: int = 100) -> list[UserRead]:
        """List users with pagination"""
        logger.debug(f"Listing users (skip={skip}, limit={limit})")
        users = db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()
        
        return [
            UserRead(
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
            for user in users
        ]