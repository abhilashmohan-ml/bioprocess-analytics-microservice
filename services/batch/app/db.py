"""Database configuration using centralized settings"""
from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from uuid import uuid4
import uuid
import logging
from datetime import datetime

# Import centralized configuration
import sys
sys.path.append('../../..')
from shared.config import settings

logger = logging.getLogger(__name__)

# Use centralized database URL and settings
DATABASE_URL = settings.database.batch_database_url

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

class Batch(Base):
    """Batch model with enhanced fields and centralized configuration"""
    __tablename__ = "batches"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(String(100), unique=True, nullable=False, index=True)
    date_time = Column(DateTime, nullable=False)
    product = Column(String(200), nullable=False)
    location = Column(String(200), nullable=False)
    process = Column(String(200), nullable=False)
    process_step = Column(String(200), nullable=False)
    qc_batch_id = Column(String(100), ForeignKey('qc_batches.qc_batch_id'), nullable=True)
    process_batch_end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Batch(id={self.id}, batch_id={self.batch_id}, product={self.product})>"

class QCBatch(Base):
    """QC Batch model with enhanced fields and centralized configuration"""
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