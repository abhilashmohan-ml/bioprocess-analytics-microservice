from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from os import getenv

DATABASE_URL = getenv("USER_DATABASE_URL", "postgresql+psycopg2://useruser:password@localhost:5432/userdb")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

class User(Base):
    __tablename__ = "users"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    department = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
