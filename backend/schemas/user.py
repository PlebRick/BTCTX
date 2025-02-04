from pydantic import BaseModel, Field
from typing import Optional

# --- User Schema for Reading Data (response model) ---
class UserRead(BaseModel):
    id: int = Field(..., description="Unique identifier for the user")
    username: str = Field(..., description="Username of the user")

    class Config:
        from_attributes = True  # For compatibility with both Pydantic v1 and v2


# --- User Schema for Creating Data (request model) ---
class UserCreate(BaseModel):
    username: str = Field(..., description="Unique username for the new user")
    password_hash: str = Field(..., description="Hashed password for secure storage")

    class Config:
        from_attributes = True


# --- User Schema for Updating Data (request model) ---
class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, description="Updated username")
    password_hash: Optional[str] = Field(None, description="Updated hashed password")

    class Config:
        from_attributes = True


# --- Additional Schema Placeholder (for Future Needs) ---
# Example: User authentication response schema with access token
class UserAuthResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(..., description="Type of token, typically 'bearer'")