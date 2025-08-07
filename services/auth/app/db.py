from sqlalchemy import create_engine, Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from os import getenv
import uuid

DATABASE_URL = getenv("AUTH_DATABASE_URL", "postgresql+psycopg2://authuser:password@localhost:5432/authdb")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ORM User table
class User(Base):
    __tablename__ = "users"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    department = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    # Add more fields as needed (approved, last_login, etc.)

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter_by(username=username).first()

def create_user_in_db(db: Session, user_dict: dict):
    user = User(**user_dict)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
