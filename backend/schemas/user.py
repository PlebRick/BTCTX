"""
backend/schemas/user.py

This module defines the Pydantic schemas for user-related data in BitcoinTX.
Since BitcoinTX is designed as a one-user application, these schemas are kept
simple but robust enough for current and future needs.

Schemas included:
  1. UserRead: Used for outputting user information in API responses.
  2. UserCreate: Used for accepting data when creating a new user (registration).
  3. UserUpdate: Used for updating an existing user's information.
  4. UserAuthResponse: Used for returning authentication details (e.g., JWT token)
     after login.

Each schema is thoroughly documented with field-level and overall comments.
"""

from pydantic import BaseModel, Field
from typing import Optional

# --- Schema for Reading User Data (Response Model) ---
class UserRead(BaseModel):
    """
    UserRead represents the structure of the user data returned by the API.

    Attributes:
      id (int): Unique identifier for the user.
      username (str): The username of the user.
    
    Note:
      - In BitcoinTX, which is a one-user application, this schema represents the
        single user's information.
    """
    id: int = Field(..., description="Unique identifier for the user")
    username: str = Field(..., description="Username of the user")

    class Config:
        # 'from_attributes = True' enables compatibility with ORM objects.
        from_attributes = True


# --- Schema for Creating a New User (Request Model) ---
class UserCreate(BaseModel):
    """
    UserCreate is used when registering a new user for BitcoinTX.

    Attributes:
      username (str): The desired unique username for the new user.
      password_hash (str): The hashed password for secure storage.
    
    Note:
      - As BitcoinTX is a one-user application, this schema will be used only once
        during the initial registration. After creation, the same record is used for authentication.
    """
    username: str = Field(..., description="Unique username for the new user")
    password_hash: str = Field(..., description="Hashed password for secure storage")

    class Config:
        from_attributes = True


# --- Schema for Updating an Existing User (Request Model) ---
class UserUpdate(BaseModel):
    """
    UserUpdate allows for partial updates to the user's information.

    Attributes:
      username (Optional[str]): The new username, if it is being updated.
      password_hash (Optional[str]): The new hashed password, if updated.
    
    Note:
      - In a one-user application like BitcoinTX, this schema is used to modify the single user's data.
      - Fields are optional to allow updating only the desired attributes.
    """
    username: Optional[str] = Field(None, description="Updated username")
    password_hash: Optional[str] = Field(None, description="Updated hashed password")

    class Config:
        from_attributes = True


# --- Schema for User Authentication Response ---
class UserAuthResponse(BaseModel):
    """
    UserAuthResponse is used to return authentication details after a successful login.

    Attributes:
      access_token (str): The JWT access token for the user.
      token_type (str): The type of token, typically 'bearer'.
    
    Note:
      - This schema is crucial for the authentication flow in BitcoinTX.
      - The client receives these details and uses the access token for subsequent requests.
    """
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(..., description="Type of token, typically 'bearer'")
