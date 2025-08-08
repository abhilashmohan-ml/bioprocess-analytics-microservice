from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from os import getenv
import uuid

DATABASE_URL = getenv("BATCH_DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Batch(Base):
    __tablename__ = "batches"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(String, unique=True, nullable=False)
    date_time = Column(DateTime, nullable=False)
    product = Column(String, nullable=False)
    location = Column(String, nullable=False)
    process = Column(String, nullable=False)
    process_step = Column(String, nullable=False)
    qc_batch_id = Column(String, ForeignKey('qc_batches.qc_batch_id'), nullable=True)
    process_batch_end_date = Column(DateTime, nullable=True)

class QCBatch(Base):
    __tablename__ = "qc_batches"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    qc_batch_id = Column(String, unique=True, nullable=False)
    date_time = Column(DateTime, nullable=False)
    product = Column(String, nullable=False)
    location = Column(String, nullable=False)
    process = Column(String, nullable=False)
    process_step = Column(String, nullable=False)
    qc_batch_end_time = Column(DateTime, nullable=True)
