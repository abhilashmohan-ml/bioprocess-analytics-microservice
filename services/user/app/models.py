from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    password: str
    role: str
    department: Optional[str]
    phone_number: Optional[str]

class UserRead(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    department: Optional[str]
    phone_number: Optional[str]
    is_active: bool
