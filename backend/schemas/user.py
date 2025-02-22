"""
backend/schemas/user.py

Defines the Pydantic schemas for user creation, update, and read. 
No direct references to double-entry ledger fields are needed here,
since a user is simply the owner of multiple Accounts.
"""

from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    """
    Shared user fields. 'username' is the primary unique identifier.
    """
    username: str

class UserCreate(UserBase):
    """
    For creating a new user. We store a hashed password,
    though the field is called 'password_hash' for direct usage.
    """
    password_hash: str

class UserUpdate(BaseModel):
    """
    Fields for updating an existing user record, all optional.
    """
    username: Optional[str] = None
    password_hash: Optional[str] = None

class UserRead(UserBase):
    """
    Schema for returning user data to clients. 
    Includes the DB 'id' but excludes the hashed password.
    """
    id: int

    class Config:
        # Let pydantic convert from ORM model
        orm_mode = True
