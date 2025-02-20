from pydantic import BaseModel, condecimal
from typing import Optional, Annotated
from datetime import datetime
from decimal import Decimal

# For consistent Enum validation (optional),
# we can import the enums from the model if desired.
# Alternatively, we can treat them as strings.
from backend.models.transaction import TransactionSource, TransactionPurpose

class TransactionBase(BaseModel):
    """
    Shared fields for creating/reading/updating transactions.
    We'll keep them optional if they don't apply to every transaction type.
    """
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None

    # Main transaction amount (always in the 'from_account' currency)
    amount: Annotated[Decimal, condecimal(max_digits=18, decimal_places=8)]

    # The transaction category (Deposit, Withdrawal, Transfer, Buy, Sell)
    type: str

    # Timestamp of the transaction
    timestamp: Optional[datetime] = None

    # Fee fields: fee_amount + fee_currency
    fee_amount: Optional[Annotated[Decimal, condecimal(max_digits=18, decimal_places=8)]] = None
    fee_currency: Optional[str] = None

    # Reintroduced deposit/withdrawal metadata
    # We can store them as Python Enums (TransactionSource/Purpose)
    # or simply as strings if you prefer looser validation.
    source: Optional[TransactionSource] = None
    purpose: Optional[TransactionPurpose] = None

    # Note: If you prefer simpler string-based fields, do:
    # source: Optional[str] = None
    # purpose: Optional[str] = None


class TransactionCreate(TransactionBase):
    """
    Fields required for creating a new transaction.
    Inherits from TransactionBase and adds extra optional tax fields.
    """
    proceeds_usd: Optional[Annotated[Decimal, condecimal(max_digits=18, decimal_places=2)]] = None
    cost_basis_usd: Optional[Annotated[Decimal, condecimal(max_digits=18, decimal_places=2)]] = None


class TransactionUpdate(BaseModel):
    """
    Fields that can be updated in an existing transaction (partial update).
    This doesn't inherit from TransactionBase, so we redefine the fields as optional.
    """
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    amount: Optional[Annotated[Decimal, condecimal(max_digits=18, decimal_places=8)]] = None
    type: Optional[str] = None
    timestamp: Optional[datetime] = None

    fee_amount: Optional[Annotated[Decimal, condecimal(max_digits=18, decimal_places=8)]] = None
    fee_currency: Optional[str] = None
    external_ref: Optional[str] = None

    proceeds_usd: Optional[Annotated[Decimal, condecimal(max_digits=18, decimal_places=2)]] = None
    cost_basis_usd: Optional[Annotated[Decimal, condecimal(max_digits=18, decimal_places=2)]] = None

    # Same reintroduced fields
    source: Optional[TransactionSource] = None
    purpose: Optional[TransactionPurpose] = None

    # If you'd prefer string-based fields:
    # source: Optional[str] = None
    # purpose: Optional[str] = None


class TransactionRead(TransactionBase):
    """
    Fields returned to the client after creating/fetching a transaction.
    Inherits from TransactionBase so it automatically includes source/purpose.
    """
    id: int
    created_at: datetime
    updated_at: datetime
    group_id: Optional[int] = None

    cost_basis_usd: Optional[Annotated[Decimal, condecimal(max_digits=18, decimal_places=2)]] = None
    proceeds_usd: Optional[Annotated[Decimal, condecimal(max_digits=18, decimal_places=2)]] = None
    realized_gain_usd: Optional[Annotated[Decimal, condecimal(max_digits=18, decimal_places=2)]] = None
    holding_period: Optional[str] = None
    is_locked: bool

    class Config:
        orm_mode = True
