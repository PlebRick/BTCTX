from sqlalchemy.orm import Session
from backend.models.user import User
from backend.schemas.user import UserCreate, UserUpdate

# --- Retrieve all users ---
def get_all_users(db: Session) -> list[User]:
    """
    Fetch all users from the database.

    Args:
        db (Session): Database session dependency.

    Returns:
        list[User]: List of all users.
    """
    return db.query(User).all()

# --- Retrieve a user by username ---
def get_user_by_username(username: str, db: Session) -> User | None:
    """
    Fetch a user by their username.

    Args:
        username (str): The username to search for.
        db (Session): Database session dependency.

    Returns:
        User | None: The user object if found, otherwise None.
    """
    return db.query(User).filter(User.username == username).first()

# --- Create a new user ---
def create_user(user_data: UserCreate, db: Session) -> User | None:
    """
    Create a new user with a hashed password.

    Args:
        user_data (UserCreate): Data for creating the new user.
        db (Session): Database session dependency.

    Returns:
        User | None: The newly created user, or None if the username already exists.
    """
    # Check if the username is already registered
    if get_user_by_username(user_data.username, db):
        return None  # Handle case where the username already exists

    # Create the new user and hash the password
    new_user = User(username=user_data.username)
    new_user.set_password(user_data.password_hash)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# --- Update an existing user ---
def update_user(user_id: int, user_data: UserUpdate, db: Session) -> User | None:
    """
    Update an existing user's data.

    Args:
        user_id (int): The ID of the user to update.
        user_data (UserUpdate): Data for updating the user.
        db (Session): Database session dependency.

    Returns:
        User | None: The updated user object, or None if not found.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None

    # Update only provided fields
    if user_data.username:
        db_user.username = user_data.username
    if user_data.password_hash:
        db_user.set_password(user_data.password_hash)

    db.commit()
    db.refresh(db_user)
    return db_user

# --- Delete a user ---
def delete_user(user_id: int, db: Session) -> bool:
    """
    Delete a user by their ID.

    Args:
        user_id (int): The ID of the user to delete.
        db (Session): Database session dependency.

    Returns:
        bool: True if the user was deleted, False if not found.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False