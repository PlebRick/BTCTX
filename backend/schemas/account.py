"""
backend/schemas/account.py

This module defines the Pydantic schemas for managing Account data in BitcoinTX.
It includes:

  1. AccountRead: Used as the response model when returning account data from the API.
     It maps to the underlying ORM model and includes fields like id, user_id, type,
     balance_usd, and balance_btc.

  2. AccountCreate: Used as the request model for creating a new account.
     It requires the user_id and the account type, and it initializes balances to 0.0 by default.

  3. AccountUpdate: Used as the request model for updating an existing account.
     All fields are optional so that you can update one or more fields without affecting the rest.

These schemas use the configuration setting 'from_attributes = True' to enable
automatic conversion from ORM objects to Pydantic models (this is analogous to using
`orm_mode = True` in Pydantic v1).
"""

from pydantic import BaseModel, Field
from typing import Optional
from backend.models.account import AccountType  # AccountType should be an Enum (e.g., Bank, Wallet, Exchange)

# --- Schema for Reading Account Data (Response Model) ---
class AccountRead(BaseModel):
    """
    AccountRead defines the structure of account data returned by the API.

    Attributes:
        id (int): Unique identifier for the account.
        user_id (int): ID of the user who owns the account.
        type (AccountType): The type of the account (e.g., Bank, Wallet, Exchange).
        balance_usd (float): The current balance in US Dollars.
        balance_btc (float): The current balance in Bitcoin.
    """
    id: int = Field(..., description="Unique identifier for the account")
    user_id: int = Field(..., description="ID of the user who owns the account")
    type: AccountType = Field(..., description="Type of the account (Bank, Wallet, Exchange)")
    balance_usd: float = Field(..., description="USD balance in the account")
    balance_btc: float = Field(..., description="BTC balance in the account")

    class Config:
        # 'from_attributes = True' enables compatibility with ORM objects.
        from_attributes = True


# --- Schema for Creating a New Account (Request Model) ---
class AccountCreate(BaseModel):
    """
    AccountCreate defines the data required to create a new account.

    Attributes:
        user_id (int): The ID of the user who will own the new account.
        type (AccountType): The type of account to be created (e.g., Bank, Wallet, Exchange).
        balance_usd (float): The initial balance in USD. Defaults to 0.0.
        balance_btc (float): The initial balance in BTC. Defaults to 0.0.
    """
    user_id: int = Field(..., description="ID of the user who will own the account")
    type: AccountType = Field(..., description="Type of the new account (Bank, Wallet, Exchange)")
    balance_usd: float = Field(0.0, description="Initial USD balance")
    balance_btc: float = Field(0.0, description="Initial BTC balance")


# --- Schema for Updating an Existing Account (Request Model) ---
class AccountUpdate(BaseModel):
    """
    AccountUpdate defines the fields that can be updated for an existing account.

    All fields are optional, allowing partial updates.
    
    Attributes:
        type (Optional[AccountType]): The updated account type.
        balance_usd (Optional[float]): The updated balance in USD.
        balance_btc (Optional[float]): The updated balance in BTC.
    """
    type: Optional[AccountType] = Field(None, description="Updated account type")
    balance_usd: Optional[float] = Field(None, description="Updated USD balance")
    balance_btc: Optional[float] = Field(None, description="Updated BTC balance")

    class Config:
        # Enable automatic conversion from ORM objects for partial updates.
        from_attributes = True
