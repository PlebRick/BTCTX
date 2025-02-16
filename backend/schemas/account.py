"""
backend/schemas/account.py

Refactored for double-entry system clarity:
  - We highlight that 'AccountType' may now include 'ExchangeUSD' and 'ExchangeBTC' if desired.
  - No direct references to transaction.account_id are used here, so no major changes.
  - We preserve the existing read/create/update structures, adding comments about usage.
"""

from pydantic import BaseModel, Field
from typing import Optional
from backend.models.account import AccountType

# -------------------------------------------------------------------
#         AccountRead (Response Model)
# -------------------------------------------------------------------

class AccountRead(BaseModel):
    """
    Returns account data to the client. Note that if the account is
    'ExchangeUSD', it primarily uses balance_usd. If it's 'ExchangeBTC',
    it primarily uses balance_btc. Other types might track one or both.
    """
    id: int = Field(..., description="Unique identifier for the account")
    user_id: int = Field(..., description="ID of the user who owns the account")
    type: AccountType = Field(..., description="Type of the account (Bank, Wallet, ExchangeUSD, ExchangeBTC)")
    balance_usd: float = Field(..., description="USD balance in the account")
    balance_btc: float = Field(..., description="BTC balance in the account")

    class Config:
        from_attributes = True


# -------------------------------------------------------------------
#         AccountCreate (Request Model)
# -------------------------------------------------------------------

class AccountCreate(BaseModel):
    """
    Used for creating a new account. With the double-entry system,
    the main difference is we may specify 'ExchangeUSD' or 'ExchangeBTC'
    if we want separate accounts for each currency on an exchange.
    By default, we still allow setting initial balances for USD or BTC.
    """
    user_id: int = Field(..., description="ID of the user who will own the account")
    type: AccountType = Field(..., description="Type of the new account (e.g. Bank, Wallet, ExchangeUSD, ExchangeBTC)")
    balance_usd: float = Field(0.0, description="Initial USD balance")
    balance_btc: float = Field(0.0, description="Initial BTC balance")


# -------------------------------------------------------------------
#         AccountUpdate (Request Model)
# -------------------------------------------------------------------

class AccountUpdate(BaseModel):
    """
    Allows partial updates to an existing account. For example, you can
    change the account type from 'ExchangeUSD' to 'Bank' if needed, or
    adjust the balances. Realistically, the system might rarely allow
    changing the type once an account is in use, but this remains flexible.
    """
    type: Optional[AccountType] = Field(None, description="Updated account type (e.g., Bank, Wallet, ExchangeUSD, ExchangeBTC)")
    balance_usd: Optional[float] = Field(None, description="Updated USD balance")
    balance_btc: Optional[float] = Field(None, description="Updated BTC balance")

    class Config:
        from_attributes = True
