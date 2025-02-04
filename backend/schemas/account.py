from pydantic import BaseModel, Field
from typing import Optional
from backend.models.account import AccountType

# --- Account Schema for Reading Data (response model) ---
class AccountRead(BaseModel):
    id: int = Field(..., description="Unique identifier for the account")
    user_id: int = Field(..., description="ID of the user who owns the account")
    type: AccountType = Field(..., description="Type of the account (Bank, Wallet, Exchange)")
    balance_usd: float = Field(..., description="USD balance in the account")
    balance_btc: float = Field(..., description="BTC balance in the account")

    class Config:
        from_attributes = True  # Use `orm_mode = True` if using Pydantic v1


# --- Account Schema for Creating Data (request model) ---
class AccountCreate(BaseModel):
    user_id: int = Field(..., description="ID of the user who will own the account")
    type: AccountType = Field(..., description="Type of the new account (Bank, Wallet, Exchange)")
    balance_usd: float = Field(0.0, description="Initial USD balance")
    balance_btc: float = Field(0.0, description="Initial BTC balance")


# --- Account Schema for Updating Data (request model) ---
class AccountUpdate(BaseModel):
    type: Optional[AccountType] = Field(None, description="Updated account type")
    balance_usd: Optional[float] = Field(None, description="Updated USD balance")
    balance_btc: Optional[float] = Field(None, description="Updated BTC balance")

    class Config:
        from_attributes = True