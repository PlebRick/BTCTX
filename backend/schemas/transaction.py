from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from backend.models.transaction import TransactionType, TransactionPurpose, TransactionSource

# --- Nested Schema: Fee ---
# Defines the fee field used in transaction forms.
class Fee(BaseModel):
    currency: str = Field(..., description="Currency of the fee (e.g., USD, BTC)")
    amount: float = Field(..., description="Amount of the fee")

# --- Schema for Reading Transaction Data ---
class TransactionRead(BaseModel):
    id: int = Field(..., description="Unique identifier for the transaction")
    account_id: int = Field(..., description="ID of the account associated with this transaction")
    type: TransactionType = Field(..., description="Type of transaction (Deposit, Withdrawal, etc.)")
    amount_usd: float = Field(..., description="Amount in USD, if applicable")
    amount_btc: float = Field(..., description="Amount in BTC, if applicable")
    timestamp: datetime = Field(..., description="Timestamp of the transaction")
    source: Optional[TransactionSource] = Field(None, description="Source of BTC deposits")
    purpose: Optional[TransactionPurpose] = Field(None, description="Purpose of BTC withdrawals")
    fee: Optional[Fee] = Field(None, description="Optional transaction fee")

    class Config:
        from_attributes = True  # Ensures ORM compatibility (use orm_mode in Pydantic v1)

# --- Schema for Creating Transaction Data ---
class TransactionCreate(BaseModel):
    account_id: int = Field(..., description="ID of the account for this transaction")
    type: TransactionType = Field(..., description="Type of transaction (Deposit, Withdrawal, etc.)")
    amount_usd: float = Field(..., description="Amount in USD")
    amount_btc: float = Field(..., description="Amount in BTC")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the transaction")
    source: Optional[TransactionSource] = Field(None, description="Source of BTC deposits")
    purpose: Optional[TransactionPurpose] = Field(None, description="Purpose of BTC withdrawals")
    fee: Optional[Fee] = Field(None, description="Transaction fee (optional)")

# --- Schema for Updating Transaction Data ---
class TransactionUpdate(BaseModel):
    type: Optional[TransactionType] = Field(None, description="Updated transaction type")
    amount_usd: Optional[float] = Field(None, description="Updated amount in USD")
    amount_btc: Optional[float] = Field(None, description="Updated amount in BTC")
    purpose: Optional[TransactionPurpose] = Field(None, description="Updated purpose for BTC withdrawals")
    source: Optional[TransactionSource] = Field(None, description="Updated source for BTC deposits")
    fee: Optional[Fee] = Field(None, description="Updated transaction fee (optional)")

    class Config:
        from_attributes = True