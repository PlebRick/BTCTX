"""
backend/services/user.py

Manages user-level operations (list, create, update, delete).
No references to ledger or transaction logic are present;
this remains separate from double-entry concerns.

Refactored to:
 - Accept a raw "password" in create_user (UserCreate)
 - Use set_password(...) to hash it before storing.
"""

from __future__ import annotations

from sqlalchemy.orm import Session
from backend.models.user import User
from backend.schemas.user import UserCreate, UserUpdate

def get_all_users(db: Session) -> list[User]:
    """
    Fetch and return all User records.
    Usually for admin or debugging in single-user apps.
    """
    return db.query(User).all()

def get_user_by_username(username: str, db: Session) -> User | None:
    """
    Return a User by username, or None if not found.
    """
    return db.query(User).filter(User.username == username).first()

def create_user(user_data: UserCreate, db: Session) -> User | None:
    """
    Create a new User record using the raw password from user_data.password.
    Automatically hashes the password via set_password.

    If username is already taken, returns None.
    """
    # Double-check duplicates
    if get_user_by_username(user_data.username, db):
        return None

    # Create a new User object
    new_user = User(username=user_data.username)

    # set_password expects a raw password; it will hash internally
    new_user.set_password(user_data.password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def update_user(user_id: int, user_data: UserUpdate, db: Session) -> User | None:
    """
    Update fields of an existing user (e.g. new username or password).
    If not found, return None.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None

    # If we have a new username, set it
    if user_data.username is not None:
        db_user.username = user_data.username

    # If we have a new raw password, hash & store it
    if user_data.password:
        db_user.set_password(user_data.password)

    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(user_id: int, db: Session) -> bool:
    """
    Delete a User by ID.
    In a multi-user environment, you might disallow this
    if the user has active ledger records. For single-user, it might be a non-issue.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False