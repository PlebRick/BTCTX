"""
backend/services/user.py

Handles user-level operations (list, create, update, delete).
No references to ledger or transaction logic are present; 
this remains separate from double-entry concerns.
"""

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
    Create a new User record. 
    The user_data should have 'username' and 'password_hash'.
    If the username is taken, we return None (or handle differently).
    """
    # Check for duplicates
    if get_user_by_username(user_data.username, db):
        return None

    # Create and store the new user
    new_user = User(username=user_data.username)
    new_user.set_password(user_data.password_hash)
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

    if user_data.username is not None:
        db_user.username = user_data.username
    if user_data.password_hash:
        db_user.set_password(user_data.password_hash)

    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(user_id: int, db: Session) -> bool:
    """
    Delete a User by ID. 
    In a multi-user environment, you might disallow this if the user
    has active ledger records. For single-user, it might be a non-issue.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False
