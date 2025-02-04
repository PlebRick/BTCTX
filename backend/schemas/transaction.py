from pydantic import BaseModel, Field
from datetime import datetime
from backend.models.transaction import TransactionType, TransactionPurpose, TransactionSource

# --- Transaction Schema for Reading Data ---
class TransactionRead(BaseModel):
    id: int
    account_id: int
    type: TransactionType
    amount_usd: float
    amount_btc: float
    timestamp: datetime
    purpose: TransactionPurpose | None = None
    source: TransactionSource | None = None

    class Config:
        # Ensure compatibility with Pydantic v2 (use 'orm_mode' if v1)
        from_attributes = True  # Use `orm_mode = True` if using Pydantic v1


# --- Transaction Schema for Creating Data ---
class TransactionCreate(BaseModel):
    account_id: int = Field(..., description="The ID of the account associated with this transaction")
    type: TransactionType = Field(..., description="The type of transaction (Deposit, Withdrawal, Transfer, etc.)")
    amount_usd: float = Field(..., description="Amount in USD, applicable for some transactions")
    amount_btc: float = Field(..., description="Amount in BTC, applicable for some transactions")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="The date and time of the transaction")
    purpose: TransactionPurpose | None = Field(None, description="Purpose of the transaction, used for BTC withdrawals")
    source: TransactionSource | None = Field(None, description="Source of the transaction, used for BTC deposits")


# --- Transaction Schema for Updating Data ---
class TransactionUpdate(BaseModel):
    type: TransactionType | None = Field(None, description="The type of transaction (optional for updates)")
    amount_usd: float | None = Field(None, description="Updated USD amount")
    amount_btc: float | None = Field(None, description="Updated BTC amount")
    purpose: TransactionPurpose | None = Field(None, description="Updated purpose for BTC withdrawals")
    source: TransactionSource | None = Field(None, description="Updated source for BTC deposits")

    class Config:
        from_attributes = True