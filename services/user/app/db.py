"""Database configuration using centralized settings"""
from sqlalchemy import create_engine, Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from uuid import uuid4
import uuid
import logging

# Import centralized configuration
import sys
sys.path.append('../../..')
from shared.config import settings

logger = logging.getLogger(__name__)

# Use centralized database URL and settings
DATABASE_URL = settings.database.user_database_url

# Create engine with centralized settings
engine = create_engine(
    DATABASE_URL,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_timeout=settings.database.pool_timeout,
    pool_recycle=settings.database.pool_recycle,
    echo=settings.database.echo
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Get database session with centralized configuration"""
    db = SessionLocal()
    try:
        logger.debug("Database session created")
        yield db
    finally:
        logger.debug("Database session closed")
        db.close()

class User(Base):
    """User model with enhanced fields and centralized configuration"""
    __tablename__ = "users"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="user")
    department = Column(String(100))
    phone_number = Column(String(20))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=__import__('datetime').datetime.utcnow)
    updated_at = Column(DateTime, default=__import__('datetime').datetime.utcnow, onupdate=__import__('datetime').datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

def get_user_by_username(db: Session, username: str):
    """Get user by username with centralized logging"""
    logger.debug(f"Looking up user by username: {username}")
    return db.query(User).filter_by(username=username).first()

def get_user_by_id(db: Session, user_id: str):
    """Get user by ID with centralized logging"""
    logger.debug(f"Looking up user by ID: {user_id}")
    return db.query(User).filter(User.id == user_id).first()

def create_user_in_db(db: Session, user_dict: dict):
    """Create user in database with centralized logging"""
    logger.info(f"Creating new user: {user_dict.get('username')}")
    user = User(**user_dict)
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"User created successfully: {user.id}")
    return user