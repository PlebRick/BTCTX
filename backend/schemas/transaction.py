from pydantic import BaseModel, condecimal
from typing import Optional, Annotated
from datetime import datetime
from decimal import Decimal

class TransactionBase(BaseModel):
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    # Use Annotated to specify a Decimal with constraints from condecimal.
    amount: Annotated[Decimal, condecimal(max_digits=18, decimal_places=8)]
    type: str  # e.g., "Deposit", "Withdrawal", "Transfer", "Buy", "Sell"
    timestamp: Optional[datetime] = None
    fee_amount: Optional[Annotated[Decimal, condecimal(max_digits=18, decimal_places=8)]] = None
    fee_currency: Optional[str] = None

class TransactionCreate(TransactionBase):
    proceeds_usd: Optional[Annotated[Decimal, condecimal(max_digits=18, decimal_places=2)]] = None
    cost_basis_usd: Optional[Annotated[Decimal, condecimal(max_digits=18, decimal_places=2)]] = None

class TransactionUpdate(BaseModel):
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

class TransactionRead(TransactionBase):
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
