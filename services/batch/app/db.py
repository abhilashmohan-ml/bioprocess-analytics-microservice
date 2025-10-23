"""Database configuration – bullet-proof, psycopg v3."""
from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey
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
# Engines – flat keys + psycopg v3 dialect
# ------------------------------------------------------------------
AUTH_DATABASE_URL = settings.AUTH_DATABASE_URL.replace("postgresql+psycopg2", "postgresql+psycopg")
USER_DATABASE_URL = settings.USER_DATABASE_URL.replace("postgresql+psycopg2", "postgresql+psycopg")
BATCH_DATABASE_URL = settings.BATCH_DATABASE_URL.replace("postgresql+psycopg2", "postgresql+psycopg")

# Auth DB engine (read-only, for FK checks)
auth_engine = create_engine(
    AUTH_DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    echo=settings.DB_ECHO,
)

# User DB engine (read-only)
user_engine = create_engine(
    USER_DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    echo=settings.DB_ECHO,
)

# Batch DB engine (read/write)
batch_engine = create_engine(
    BATCH_DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    echo=settings.DB_ECHO,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=batch_engine)
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
# Models – unchanged
# ------------------------------------------------------------------
class Batch(Base):
    __tablename__ = "batches"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(String(100), unique=True, nullable=False, index=True)
    date_time = Column(DateTime, nullable=False)
    product = Column(String(200), nullable=False)
    location = Column(String(200), nullable=False)
    process = Column(String(200), nullable=False)
    process_step = Column(String(200), nullable=False)
    qc_batch_id = Column(String(100), ForeignKey("qc_batches.qc_batch_id"), nullable=True)
    process_batch_end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Batch(id={self.id}, batch_id={self.batch_id}, product={self.product})>"


class QCBatch(Base):
    __tablename__ = "qc_batches"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    qc_batch_id = Column(String(100), unique=True, nullable=False, index=True)
    date_time = Column(DateTime, nullable=False)
    product = Column(String(200), nullable=False)
    location = Column(String(200), nullable=False)
    process = Column(String(200), nullable=False)
    process_step = Column(String(200), nullable=False)
    qc_batch_end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<QCBatch(id={self.id}, qc_batch_id={self.qc_batch_id}, product={self.product})>"