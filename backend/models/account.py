"""
backend/models/account.py

This module defines the Account model for BitcoinTX.
Each Account references a single User via user_id (NOT NULL).
"""

from enum import Enum
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class AccountType(Enum):
    """
    Older design referencing "Bank", "Wallet", "ExchangeUSD", "ExchangeBTC".
    In the current design, we store 'name' and 'currency' directly,
    so you may or may not use this enum at runtime.
    """
    Bank = "Bank"
    Wallet = "Wallet"
    ExchangeUSD = "ExchangeUSD"
    ExchangeBTC = "ExchangeBTC"

class Account(Base):
    __tablename__ = "accounts"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Link to user (cannot be null)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # A unique name for the account, e.g. "Bank", "Wallet", "ExchangeUSD"...
    name = Column(String, unique=True, nullable=False)

    # The currency this account holds: "USD" or "BTC"
    currency = Column(String, nullable=False, default="USD")

    # Relationship to the owning User
    user = relationship("User", back_populates="accounts")

    # These relationships track transactions where this account is the 'from' or 'to' side
    transactions_from = relationship("Transaction", foreign_keys="[Transaction.from_account_id]")
    transactions_to   = relationship("Transaction", foreign_keys="[Transaction.to_account_id]")

    def __repr__(self):
        return f"<Account(id={self.id}, user_id={self.user_id}, name={self.name}, currency={self.currency})>"
