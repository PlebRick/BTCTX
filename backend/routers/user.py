"""
backend/routers/user.py

Handles user-related endpoints (registration, listing users, etc.).
Now uses session-based logic (in main.py), so we've removed JWT references.

Refactored to add:
 - PATCH /users/{user_id}: partial update of username/password
 - DELETE /users/{user_id}: remove a user entirely
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.schemas.user import UserCreate, UserRead, UserUpdate
from backend.services.user import (
    get_user_by_username,
    create_user,
    get_all_users,
    update_user as update_user_service,
    delete_user as delete_user_service
)
from backend.database import SessionLocal

router = APIRouter(tags=["users"])

def get_db():
    """
    Provide a DB session for user endpoints.
    Typically you might use 'get_db' from database.py,
    but here we define it inline for completeness.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=UserRead)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user by:
      1) Checking if the username is already taken.
      2) Hashing the provided password (handled in create_user).
      3) Inserting the new user record in the DB.
    
    Returns a UserRead schema (excluding password hash).
    Raises 400 if username is taken.
    """
    existing_user = get_user_by_username(user.username, db)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    new_user = create_user(user, db)
    if not new_user:
        raise HTTPException(status_code=500, detail="Unable to create user")

    return new_user

@router.get("/", response_model=List[UserRead])
def get_users(db: Session = Depends(get_db)):
    """
    Retrieve all registered users in the system, for debugging or admin usage.
    (In single-user mode, you likely won't use this in production.)
    """
    return get_all_users(db)

@router.patch("/users/{user_id}", response_model=UserRead)
def patch_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    """
    Partially update a user's fields (username or password) using UserUpdate.
    If the user isn't found, returns 404.
    On success, returns the updated user record (UserRead).
    
    Example JSON body:
      {
        "username": "NewName",
        "password": "NewPass123"
      }
    """
    updated_user = update_user_service(user_id, user_data, db)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found.")
    return updated_user

@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete an existing user by ID. If user doesn't exist, raises 404.
    Returns 204 No Content on successful deletion.
    """
    success = delete_user_service(user_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or cannot be deleted.")
    return