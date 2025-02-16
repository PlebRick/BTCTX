"""
schemas/transaction.py

Refactored for double-entry Plan B:
  - Removed the single 'account_id' in favor of 'from_account_id' and 'to_account_id'.
  - Retained existing fields: amount_usd, amount_btc, fee, cost_basis_usd, source, purpose, etc.
  - The user must now provide from_account_id and to_account_id on creation, matching the new model.
  - For reading, we display from_account_id and to_account_id in the output, instead of account_id.
"""

from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime
# We'll import the enums from the models as before
from backend.models.transaction import TransactionType, TransactionPurpose, TransactionSource

# -------------------------------------------------------------------
#        TransactionRead (for output)
# -------------------------------------------------------------------

class TransactionRead(BaseModel):
    """
    Schema for outputting transaction data in double-entry format.
    Key Change:
      - Removed the single 'account_id' field.
      - Added from_account_id and to_account_id.
    Other fields (fee, cost_basis_usd, etc.) remain the same.

    Explanation:
      - 'from_account_id': numeric ID of the account where funds originated.
      - 'to_account_id': numeric ID of the account where funds were credited.
      - 'amount_usd' and 'amount_btc': total amounts in each currency (any can be 0).
    """
    id: int

    # Replaced account_id with separate references
    from_account_id: int
    to_account_id: int

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
        Convert ORM object to dict if needed, ensuring numeric fields
        are properly retrieved from the SQLAlchemy model.
        """
        if not isinstance(values, dict):
            try:
                # Pull column values directly from the ORM object if possible
                values = {
                    col.name: getattr(values, col.name)
                    for col in values.__table__.columns
                }
            except AttributeError:
                pass
        return values

    class Config:
        from_attributes = True  # pydantic v2 style: read from ORM directly

# -------------------------------------------------------------------
#        TransactionCreate (for creating new transactions)
# -------------------------------------------------------------------

class TransactionCreate(BaseModel):
    """
    Schema for creating a new transaction in double-entry form.
    Key Changes:
      - Removed single 'account_id'.
      - Added 'from_account_id' and 'to_account_id'.
      - Keep amount_usd, amount_btc, fee, cost_basis_usd, etc.
      - type, source, purpose remain enumerations from the model.

    Example usage:
      - For a deposit: from_account_id might be an 'External' account; to_account_id the user's wallet.
      - For a withdrawal: from_account_id = user's wallet; to_account_id = 'External'.
      - For a transfer: from_account_id = A, to_account_id = B (two internal accounts).
      - For a buy (ExchangeUSD -> ExchangeBTC): from_account_id = ExchangeUSD, to_account_id = ExchangeBTC, etc.
    """
    from_account_id: int
    to_account_id: int

    type: TransactionType

    # Amounts default to 0 if not used
    amount_usd: float = 0.0
    amount_btc: float = 0.0

    # Timestamp with default to current UTC
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Defaults to the current UTC time."
    )

    source: Optional[TransactionSource] = TransactionSource.NA
    purpose: Optional[TransactionPurpose] = TransactionPurpose.NA

    fee: Optional[float] = 0.0
    cost_basis_usd: Optional[float] = 0.0

    is_locked: bool = False

    class Config:
        from_attributes = True

# -------------------------------------------------------------------
#        TransactionUpdate (for patching existing transactions)
# -------------------------------------------------------------------

class TransactionUpdate(BaseModel):
    """
    Schema for updating an existing transaction.
    All fields are optional (for partial updates).
    Not all fields may be changeable if the transaction is locked
    or if the logic disallows changing from_account_id/to_account_id post-creation.
    """
    from_account_id: Optional[int]
    to_account_id: Optional[int]

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
