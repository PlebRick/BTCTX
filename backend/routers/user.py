"""
backend/routers/user.py

Handles user-related endpoints (registration, listing users, login).
No direct references to double-entry logic here, as user accounts 
are managed in 'account.py'. This remains nearly unchanged from 
the simpler approach.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List

from backend.schemas.user import UserCreate, UserRead
from backend.services.user import (
    get_user_by_username,
    create_user,
    get_all_users
)
from backend.utils.auth import create_access_token
from backend.database import SessionLocal

router = APIRouter(tags=["users"])

def get_db():
    """
    Provide a DB session for user endpoints.
    Typically you might use 'get_db' from database.py,
    but here we define it inline if desired.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user credentials and return a JWT token if valid.
    The user logic is separate from double-entry ledger concerns.
    """
    user = get_user_by_username(form_data.username, db)
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserRead)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new User. If username is already taken, return 400.
    This does not directly affect ledger logic, but each user 
    can later own multiple accounts.
    """
    if get_user_by_username(user.username, db):
        raise HTTPException(status_code=400, detail="Username already registered")
    return create_user(user, db)

@router.get("/", response_model=List[UserRead])
def get_users(db: Session = Depends(get_db)):
    """
    Retrieve all registered users in the system, for debugging or admin usage.
    Still not directly referencing double-entry logic.
    """
    return get_all_users(db)
