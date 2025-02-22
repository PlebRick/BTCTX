"""
backend/schemas/account.py

Defines Pydantic schemas for creating, updating, and reading Account objects.
Since the double-entry logic primarily lives in LedgerEntry or Transaction,
we typically don't embed ledger info in the Account schemas directly, but
you can if you want to show related ledger_entries.

We include user_id in AccountCreate because each Account belongs to a specific User.
"""

from pydantic import BaseModel
from typing import Optional

class AccountBase(BaseModel):
    """
    Common fields for an Account, used by create/read/update.
    - 'name': a label like "Bank", "BTC Wallet", "BTC Fees"
    - 'currency': "USD" or "BTC" in typical usage
    """
    name: str
    currency: str

class AccountCreate(AccountBase):
    """
    Schema for creating a new Account. We require user_id because
    the DB schema has user_id as NOT NULL, referencing which user owns it.
    """
    user_id: int

class AccountUpdate(BaseModel):
    """
    Schema for updating an existing Account record.
    Currently only 'name' or 'currency' can be updated, both optional.
    """
    name: Optional[str] = None
    currency: Optional[str] = None

class AccountRead(AccountBase):
    """
    Schema returned after fetching an Account.
    Includes the DB-generated 'id' and the 'user_id' that references
    which user owns this account.
    """
    id: int
    user_id: int

    class Config:
        # For returning data from ORM, ensure we convert properly
        # pydantic v2 uses 'from_attributes' or 'orm_mode' for model conversion
        from_attributes = True
