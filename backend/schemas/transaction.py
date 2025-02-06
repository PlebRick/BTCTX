"""
backend/schemas/transaction.py

This module defines the Pydantic schemas for BitcoinTX transaction data.

It includes:
  - Fee: A nested schema representing the fee details for a transaction.
  - TransactionRead: The response model used when returning transaction data.
      It assembles fee details (stored in separate ORM columns: fee_currency and fee_amount)
      into a nested fee object using a model validator.
  - TransactionCreate: The request model for creating a new transaction.
  - TransactionUpdate: The request model for updating an existing transaction.

IMPORTANT:
  - The underlying ORM model (in backend/models/transaction.py) must include the
    columns 'fee_currency' and 'fee_amount'. If these columns are missing from the
    database, you'll encounter errors.
  - After updating your ORM model, reinitialize the database (delete the old file and run
    the create_db script) to apply the new schema.
"""

from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime
from backend.models.transaction import TransactionType, TransactionPurpose, TransactionSource

# --- Nested Schema: Fee ---
class Fee(BaseModel):
    """
    Represents the fee details for a transaction.
    
    Attributes:
      currency (str): The currency of the fee (e.g., USD, BTC).
      amount (float): The fee amount.
    """
    currency: str = Field(..., description="Currency of the fee (e.g., USD, BTC)")
    amount: float = Field(..., description="Amount of the fee")


# --- Schema for Reading Transaction Data ---
class TransactionRead(BaseModel):
    """
    Schema for outputting transaction data in API responses.
    
    This schema expects that the underlying ORM model for transactions includes
    separate columns 'fee_currency' and 'fee_amount'. A model validator then assembles
    these columns into a nested 'fee' object.

    Attributes:
      id (int): Unique identifier for the transaction.
      account_id (int): ID of the account associated with this transaction.
      type (TransactionType): The type of transaction (Deposit, Withdrawal, etc.).
      amount_usd (float): Amount in USD (if applicable).
      amount_btc (float): Amount in BTC (if applicable).
      timestamp (datetime): When the transaction occurred.
      source (Optional[TransactionSource]): Source of BTC deposits.
      purpose (Optional[TransactionPurpose]): Purpose of BTC withdrawals.
      fee (Optional[Fee]): A nested fee object constructed from fee_currency and fee_amount.
    """
    id: int = Field(..., description="Unique identifier for the transaction")
    account_id: int = Field(..., description="ID of the account associated with this transaction")
    type: TransactionType = Field(..., description="Type of transaction (Deposit, Withdrawal, etc.)")
    amount_usd: float = Field(..., description="Amount in USD, if applicable")
    amount_btc: float = Field(..., description="Amount in BTC, if applicable")
    timestamp: datetime = Field(..., description="Timestamp of the transaction")
    source: Optional[TransactionSource] = Field(None, description="Source of BTC deposits")
    purpose: Optional[TransactionPurpose] = Field(None, description="Purpose of BTC withdrawals")
    fee: Optional[Fee] = Field(None, description="Optional transaction fee")

    @model_validator(mode="before")
    def assemble_fee(cls, values) -> dict:
        """
        Assemble the nested fee object from separate ORM columns.

        This validator runs before model instantiation. It first ensures that the input
        is a dictionary. If not (i.e. if an ORM object is provided), it converts the object
        to a dictionary by iterating over its table columns. Then, it checks for the keys
        'fee_currency' and 'fee_amount'. If either is present, it creates a nested 'fee'
        dictionary from them.

        Args:
            values: The raw input data (either a dict or an ORM object).

        Returns:
            dict: The updated data dictionary with a nested 'fee' key if applicable.
        """
        # If values is not a dict, attempt to convert the ORM object to a dict.
        if not isinstance(values, dict):
            try:
                # Assuming the ORM object has a __table__ attribute, extract column values.
                values = {col.name: getattr(values, col.name) for col in values.__table__.columns}
            except AttributeError:
                # If conversion fails, return the values as-is.
                return values

        fee_currency = values.get("fee_currency")
        fee_amount = values.get("fee_amount")
        if fee_currency is not None or fee_amount is not None:
            values["fee"] = {"currency": fee_currency, "amount": fee_amount}
        return values

    class Config:
        # Enable compatibility with ORM objects (similar to orm_mode=True in Pydantic v1)
        from_attributes = True


# --- Schema for Creating Transaction Data ---
class TransactionCreate(BaseModel):
    """
    Schema for creating a new transaction.
    
    The fields provided here are required to insert a new transaction into the database.
    The timestamp defaults to the current UTC time if not provided.
    
    Attributes:
      account_id (int): ID of the account for this transaction.
      type (TransactionType): Transaction type.
      amount_usd (float): Transaction amount in USD.
      amount_btc (float): Transaction amount in BTC.
      timestamp (datetime): When the transaction occurred (defaults to now).
      source (Optional[TransactionSource]): Source for BTC deposits.
      purpose (Optional[TransactionPurpose]): Purpose for BTC withdrawals.
      fee (Optional[Fee]): Fee details, if any.
    """
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
    """
    Schema for updating an existing transaction.
    
    Only the fields provided in the update request will be modified.
    
    Attributes:
      type (Optional[TransactionType]): Updated transaction type.
      amount_usd (Optional[float]): Updated amount in USD.
      amount_btc (Optional[float]): Updated amount in BTC.
      purpose (Optional[TransactionPurpose]): Updated purpose for withdrawals.
      source (Optional[TransactionSource]): Updated source for deposits.
      fee (Optional[Fee]): Updated fee details, if any.
    """
    type: Optional[TransactionType] = Field(None, description="Updated transaction type")
    amount_usd: Optional[float] = Field(None, description="Updated amount in USD")
    amount_btc: Optional[float] = Field(None, description="Updated amount in BTC")
    purpose: Optional[TransactionPurpose] = Field(None, description="Updated purpose for BTC withdrawals")
    source: Optional[TransactionSource] = Field(None, description="Updated source for BTC deposits")
    fee: Optional[Fee] = Field(None, description="Updated transaction fee (optional)")

    class Config:
        from_attributes = True