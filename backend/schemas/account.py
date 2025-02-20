"""
backend/schemas/account.py

Refactored to retain user_id in the Account model.
We need user_id in AccountCreate, because the DB requires it (NOT NULL).
"""

from pydantic import BaseModel
from typing import Optional

class AccountBase(BaseModel):
    """
    Common fields shared by create/read/update.
    'name' is a human-readable label (e.g. "Bank", "Wallet"),
    'currency' must be "USD" or "BTC" in this system.
    """
    name: str
    currency: str

class AccountCreate(AccountBase):
    """
    Fields required to create a new Account.
    We must include user_id because the DB schema has
    user_id = Column(..., nullable=False).
    """
    user_id: int

class AccountUpdate(BaseModel):
    """
    Fields optional for updating an existing Account.
    """
    name: Optional[str] = None
    currency: Optional[str] = None
    # In most cases, user_id isn't updated after creation, so we omit it here.
    # If you do want to allow changing which user owns the account,
    # you could add `user_id: Optional[int] = None`.

class AccountRead(AccountBase):
    """
    Returned after retrieving an Account.
    Includes the DB-generated 'id' and also which user owns it.
    """
    id: int
    user_id: int

    class Config:
        # pydantic v2 uses 'from_attributes' instead of 'orm_mode'
        # but if you are under pydantic v2, you might see a deprecation warning.
        # For backward compatibility, you can keep it as 'orm_mode = True'
        from_attributes = True
