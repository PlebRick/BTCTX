"""
schemas/transaction.py

Pydantic schemas for Transaction data.
 - Updated to include costBasisUSD.
 - Removed fee_currency references in favor of a single 'fee' field.
 - Optional source/purpose with "N/A" as default if needed.
 - We treat datetime as UTC for the 'timestamp'.
"""

from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime
from backend.models.transaction import TransactionType, TransactionPurpose, TransactionSource

# --- Nested Schema: Fee removed, we now store fee in a single field. ---

# --- Reading Transaction Data ---
class TransactionRead(BaseModel):
    """
    Schema for outputting transaction data.
    Includes costBasisUSD, a single fee field, etc.
    """
    id: int
    account_id: int
    type: TransactionType
    amount_usd: float
    amount_btc: float
    timestamp: datetime
    source: Optional[TransactionSource] = TransactionSource.NA
    purpose: Optional[TransactionPurpose] = TransactionPurpose.NA
    fee: Optional[float] = 0.0
    cost_basis_usd: Optional[float] = 0.0
    is_locked: bool

    @model_validator(mode="before")
    def convert_orm(cls, values):
        """
        Convert ORM object to dict if needed.
        Also ensure numeric fields are properly handled.
        """
        if not isinstance(values, dict):
            try:
                values = {
                    col.name: getattr(values, col.name)
                    for col in values.__table__.columns
                }
            except AttributeError:
                pass
        return values

    class Config:
        from_attributes = True  # Allows reading from ORM objects in Pydantic v2


# --- Creating a New Transaction ---
class TransactionCreate(BaseModel):
    """
    Schema for creating a new transaction.
    - We only keep one fee field (USD).
    - costBasisUSD is optional but relevant for BTC deposits.
    """
    account_id: int
    type: TransactionType
    amount_usd: float = 0.0
    amount_btc: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Stored as UTC")
    source: Optional[TransactionSource] = TransactionSource.NA
    purpose: Optional[TransactionPurpose] = TransactionPurpose.NA
    fee: Optional[float] = 0.0  # in USD
    cost_basis_usd: Optional[float] = 0.0
    is_locked: bool = False  # new field, though typically not set at creation

    class Config:
        from_attributes = True


# --- Updating an Existing Transaction ---
class TransactionUpdate(BaseModel):
    """
    Schema for updating a transaction.
    All fields optional so we can patch what the user provides.
    """
    type: Optional[TransactionType]
    amount_usd: Optional[float]
    amount_btc: Optional[float]
    timestamp: Optional[datetime]
    source: Optional[TransactionSource]
    purpose: Optional[TransactionPurpose]
    fee: Optional[float]
    cost_basis_usd: Optional[float]
    is_locked: Optional[bool]

    class Config:
        from_attributes = True
