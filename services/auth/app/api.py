from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .models import RegisterUserRequest, LoginRequest, Token, TokenData
from .auth import AuthService
from .db import get_db

router = APIRouter()

@router.post("/register", status_code=201, summary="Register a new user")
def register(payload: RegisterUserRequest, db: Session = Depends(get_db)):
    """
    Register a new user. Validates for duplicates and stores hashed password.
    """
    try:
        AuthService.register_user(db, payload)
        return {"msg": "User registered successfully"}
    except ValueError as ve:
        raise HTTPException(400, detail=str(ve))
    except Exception as e:
        raise HTTPException(500, detail=f"Internal error: {e}")

@router.post("/login", response_model=Token, summary="User login for JWT token")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Log a user in, returning a JWT token if credentials are correct.
    """
    token = AuthService.login(db, payload)
    if not token:
        raise HTTPException(401, detail="Invalid credentials")
    return token

@router.get("/verify", response_model=TokenData, summary="Check/verify JWT token")
def verify(token: str):
    """
    Verify a JWT token and return its contents (used internally and by gateway).
    """
    try:
        return AuthService.verify_token(token)
    except Exception:
        raise HTTPException(401, detail="Invalid token")

