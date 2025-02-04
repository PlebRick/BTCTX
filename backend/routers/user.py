from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List

from backend.schemas.user import UserCreate, UserRead
from backend.services.user import get_user_by_username, create_user, get_all_users
from backend.utils.auth import create_access_token  # Import JWT function from utils
from backend.database import SessionLocal

# --- Initialize Router ---
router = APIRouter()

# --- Dependency to get the database session ---
def get_db():
    """
    Provides a database session for dependency injection.

    Yields:
        Session: SQLAlchemy session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Routes for User Management ---

# --- POST: Login and get access token ---
@router.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate the user and issue a JWT access token.

    Args:
        form_data (OAuth2PasswordRequestForm): User login credentials.
        db (Session): Database session.

    Returns:
        dict: JWT access token and token type.
    """
    user = get_user_by_username(form_data.username, db)
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- POST: Register a new user ---
@router.post("/register", response_model=UserRead)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user (for testing or administrative purposes).

    Args:
        user (UserCreate): User registration data.
        db (Session): Database session.

    Returns:
        UserRead: The created user.
    """
    if get_user_by_username(user.username, db):
        raise HTTPException(status_code=400, detail="Username already registered")

    return create_user(user, db)

# --- GET: Retrieve all users (for development or testing) ---
@router.get("/", response_model=List[UserRead])
def get_users(db: Session = Depends(get_db)):
    """
    Retrieve all users (for development and debugging).

    Args:
        db (Session): Database session.

    Returns:
        List[UserRead]: List of all registered users.
    """
    return get_all_users(db)

