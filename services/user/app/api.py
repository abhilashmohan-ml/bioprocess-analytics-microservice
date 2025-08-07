from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .models import UserCreate, UserRead
from .users import UserService
from .db import get_db

router = APIRouter()

@router.post("/users/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = UserService.create_user(db, payload)
    return user

@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = UserService.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/healthz")
def healthz():
    return {"status": "ok"}

