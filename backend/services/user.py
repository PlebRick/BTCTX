"""
services/user.py

Refactored for consistency with the double-entry system:
  - No direct references to single-entry transactions are present,
    so no structural changes are necessary.
  - We simply confirm that multiple accounts (Bank, Wallet, etc.) are
    still supported per user in the new design.
"""

from sqlalchemy.orm import Session

from backend.models.user import User
from backend.schemas.user import UserCreate, UserUpdate

def get_all_users(db: Session) -> list[User]:
    """
    Fetch all users from the database.
    No change needed for double-entry, as this deals solely with user records.
    """
    return db.query(User).all()

def get_user_by_username(username: str, db: Session) -> User | None:
    """
    Fetch a user by their username.
    Remains unchanged; no transaction references here.
    """
    return db.query(User).filter(User.username == username).first()

def create_user(user_data: UserCreate, db: Session) -> User | None:
    """
    Create a new user with a hashed password.
    - We continue to allow multiple accounts per user in the new design.
    - No direct transaction references, so no structural adjustments needed.
    """
    # Check if the username already exists
    if get_user_by_username(user_data.username, db):
        return None  # or handle duplicates differently

    # Create the new user and hash the password
    new_user = User(username=user_data.username)
    new_user.set_password(user_data.password_hash)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def update_user(user_id: int, user_data: UserUpdate, db: Session) -> User | None:
    """
    Update an existing user's data (e.g. username or password).
    No changes for double-entry logic.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None

    # Only update provided fields
    if user_data.username is not None:
        db_user.username = user_data.username
    if user_data.password_hash:
        db_user.set_password(user_data.password_hash)

    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(user_id: int, db: Session) -> bool:
    """
    Delete a user by ID.
    This remains straightforward; if you'd like to prevent deletion of a user
    with existing transactions, you'd implement that logic in a future step.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False
