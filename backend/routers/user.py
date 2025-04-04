# FILE: backend/routers/user.py

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List

# Pydantic schemas for user creation, reading, and updating
from backend.schemas.user import UserCreate, UserRead, UserUpdate

# Service functions that interact with the database
from backend.services.user import (
    get_all_users,
    get_user_by_username,
    create_user,
    update_user as update_user_service,
    delete_user as delete_user_service
)

# Database session provider
from backend.database import SessionLocal

# Create a FastAPI router instance with the "users" tag for API documentation
router = APIRouter(tags=["users"])

def get_db():
    """
    Provide a database session for user endpoints.
    Yields a SessionLocal instance and ensures it is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=UserRead)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user: POST /api/users/register

    Enforces a single-user system:
    1. If any user exists, blocks registration (400 error).
    2. Checks if the username is taken (redundant in single-user system but kept for flexibility).
    3. Creates the user with a hashed password via create_user and returns the UserRead schema.

    Best Practices:
    - Password complexity: Ensure UserCreate schema or create_user enforces IRS Publication 1075 requirements.
    - Secure storage: Verify create_user uses strong hashing (e.g., bcrypt).
    """
    # Check if any user exists (single-user limit)
    existing_users = get_all_users(db)
    if existing_users:
        raise HTTPException(
            status_code=400,
            detail="Only one user allowed. A user already exists."
        )

    # Check if this username is taken (redundant but retained for clarity)
    existing_user = get_user_by_username(user.username, db)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )

    # Create the user record
    new_user = create_user(user, db)
    if not new_user:
        raise HTTPException(
            status_code=500,
            detail="Unable to create user"
        )

    return new_user

@router.get("/", response_model=List[UserRead])
def get_users(db: Session = Depends(get_db)):
    print("✅ get_users() called")
    return get_all_users(db)

@router.patch("/{user_id}", response_model=UserRead)
def patch_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    """
    Partially update a user's fields: PATCH /api/users/{user_id}

    - Updates username or password based on the UserUpdate schema.
    - Returns the updated user (UserRead schema).
    - Raises a 404 error if the user is not found.

    Best Practices:
    - Audit logging: Implement logging in update_user_service for compliance audits.
    """
    updated_user = update_user_service(user_id, user_data, db)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found.")
    return updated_user

@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Delete a user by ID: DELETE /api/users/{user_id}

    - Deletes the user if found.
    - Clears the session afterward.
    - Returns 204 No Content on success.
    - Raises a 404 error if the user is not found or cannot be deleted.
    """
    success = delete_user_service(user_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or cannot be deleted.")

    # ✅ Clear the session after successful deletion
    request.session.clear()
    return

@router.get("/protected")
def protected_route(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    print("🔐 /protected called, user_id:", user_id)  # ADD THIS
    if not user_id:
        raise HTTPException(status_code=403, detail="Not authenticated")

    from backend.models.user import User

    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    print("✅ Returning username:", user.username)  # ADD THIS
    return {"username": user.username}