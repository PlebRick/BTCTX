"""
routers/user.py

Refactored to confirm compatibility with the double-entry system.
 - This router handles user registration, authentication, and listing.
 - No direct references to single-account logic or transaction fields,
   so no structural updates are required.
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
from backend.utils.auth import create_access_token  # JWT function from utils
from backend.database import SessionLocal

# --- Initialize Router ---
router = APIRouter()

def get_db():
    """
    Provides a database session for dependency injection.
    Yields a SQLAlchemy session and closes it afterward.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------------------------------------------
#  Login / Token Endpoint
# -------------------------------------------------------------------

@router.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate the user and issue a JWT access token.
    Unaffected by double-entry; user verification remains unchanged.
    """
    user = get_user_by_username(form_data.username, db)
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# -------------------------------------------------------------------
#  Register Endpoint
# -------------------------------------------------------------------

@router.post("/register", response_model=UserRead)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user. No changes needed for double-entry.
    If the username already exists, return error 400.
    """
    if get_user_by_username(user.username, db):
        raise HTTPException(status_code=400, detail="Username already registered")
    return create_user(user, db)

# -------------------------------------------------------------------
#  List Users Endpoint
# -------------------------------------------------------------------

@router.get("/", response_model=List[UserRead])
def get_users(db: Session = Depends(get_db)):
    """
    Retrieve all users for development/debugging.
    Still valid in double-entry; no transaction references here.
    """
    return get_all_users(db)
