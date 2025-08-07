from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class RegisterUserRequest(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    role: str
    department: str
    phone_number: str

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

    def get_uuid(self) -> Optional[UUID]:
        return UUID(self.user_id) if self.user_id else None
