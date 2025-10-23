"""Database configuration – bullet-proof, psycopg v3."""
from sqlalchemy import create_engine, Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from uuid import uuid4
import uuid
import logging
from datetime import datetime

# shared flat config
from shared.config import settings

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Engine – uses FLAT key + psycopg v3 dialect
# ------------------------------------------------------------------
DATABASE_URL = settings.AUTH_DATABASE_URL.replace(
    "postgresql+psycopg2", "postgresql+psycopg"
)  # ensures v3 driver

engine = create_engine(
    DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    echo=settings.DB_ECHO,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Get database session – flat config."""
    db = SessionLocal()
    try:
        logger.debug("Database session created")
        yield db
    finally:
        logger.debug("Database session closed")
        db.close()


# ------------------------------------------------------------------
# User model – unchanged
# ------------------------------------------------------------------
class User(Base):
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
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


# ------------------------------------------------------------------
# CRUD helpers – unchanged
# ------------------------------------------------------------------
def get_user_by_username(db: Session, username: str):
    logger.debug(f"Looking up user by username: {username}")
    return db.query(User).filter_by(username=username).first()


def get_user_by_id(db: Session, user_id: str):
    logger.debug(f"Looking up user by ID: {user_id}")
    return db.query(User).filter(User.id == user_id).first()


def create_user_in_db(db: Session, user_dict: dict):
    logger.info(f"Creating new user: {user_dict.get('username')}")
    user = User(**user_dict)
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"User created successfully: {user.id}")
    return user