"""
backend/routers/user.py

Handles user-related endpoints (registration, listing users, etc.).
Enforces a single-user limit: if any user already exists, no new registration is allowed.

Key points:
 - @router.post("/register"): final route is POST /api/users/register (due to prefix in main.py)
 - @router.get("/"): final route is GET /api/users
 - @router.patch("/users/{user_id}"): final route is PATCH /api/users/users/{user_id}
 - @router.delete("/users/{user_id}"): final route is DELETE /api/users/users/{user_id}

If you prefer /api/users/{user_id} for PATCH/DELETE, remove "users/" in those decorators.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

# Pydantic schemas for user creation/read/update
from backend.schemas.user import UserCreate, UserRead, UserUpdate

# Service functions that interact with the DB
from backend.services.user import (
    get_all_users,
    get_user_by_username,
    create_user,
    update_user as update_user_service,
    delete_user as delete_user_service
)

# Database session provider
from backend.database import SessionLocal

# Create a FastAPI router instance
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
    Single-user registration endpoint: POST /api/users/register

    1) If any user already exists, block new registration (single-user system).
    2) If the requested username is already taken, return 400 (edge case).
    3) Hash the provided password (handled in create_user) and create the user.

    Returns a UserRead schema (excluding the password hash).
    """

    # 1) Check if *any* user exists (single-user limit).
    existing_users = get_all_users(db)
    if existing_users:
        raise HTTPException(
            status_code=400,
            detail="Only one user allowed. A user already exists."
        )

    # 2) Check if this exact username is taken (paranoia check).
    #    Technically, if there's "any" user, we already blocked above.
    #    But let's keep it for clarity or if you ever allow multiple users in the future.
    existing_user = get_user_by_username(user.username, db)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )

    # 3) Create the user record.
    new_user = create_user(user, db)
    if not new_user:
        raise HTTPException(
            status_code=500,
            detail="Unable to create user"
        )

    return new_user

@router.get("/", response_model=List[UserRead])
def get_users(db: Session = Depends(get_db)):
    """
    Retrieve all registered users: GET /api/users
    Mainly for debugging or to confirm the single-user environment.
    """
    return get_all_users(db)

@router.patch("/users/{user_id}", response_model=UserRead)
def patch_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    """
    Partially update a user's fields (username or password) using UserUpdate.
    If the user isn't found, returns 404.
    On success, returns the updated user record (UserRead).

    Final route: PATCH /api/users/users/{user_id}
      (Remove 'users/' if you want PATCH /api/users/{user_id}).
    """
    updated_user = update_user_service(user_id, user_data, db)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found.")
    return updated_user

@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete an existing user by ID.
    Final route: DELETE /api/users/users/{user_id}
      (Remove 'users/' if you want /api/users/{user_id}).

    Returns 204 No Content on successful deletion, or 404 if not found.
    """
    success = delete_user_service(user_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or cannot be deleted.")
    return