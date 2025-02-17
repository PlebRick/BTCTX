"""
backend/schemas/account.py

Pydantic schemas for Account data.
Defines models for creating, updating, and reading Account objects.
"""

from pydantic import BaseModel
from typing import Optional

class AccountBase(BaseModel):
    name: str
    currency: str  # Must be "USD" or "BTC"

class AccountCreate(AccountBase):
    pass

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    currency: Optional[str] = None

class AccountRead(AccountBase):
    id: int

    class Config:
        orm_mode = True
