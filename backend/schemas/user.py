"""
backend/schemas/user.py

Defines Pydantic models (schemas) for user-related data.
Import only from standard libraries or pydantic—do NOT import from
routers or services to avoid circular dependencies.
"""

from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    """
    Base user fields. Shared logic or validations can go here.
    """
    username: str

class UserCreate(UserBase):
    """
    Schema for creating a new user.
    Includes the password field (hashed later in the model).
    """
    password_hash: str

class UserUpdate(BaseModel):
    """
    Schema for updating user data. The username might be optional if only
    changing the password, or vice versa.
    """
    username: Optional[str] = None
    password_hash: Optional[str] = None

class UserRead(UserBase):
    """
    Schema for reading a user's data back to the client.
    Typically includes an ID and excludes the password hash.
    """
    id: int

    class Config:
        orm_mode = True
