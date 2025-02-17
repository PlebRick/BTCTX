"""
backend/models/account.py

This module defines the Account model for BitcoinTX.
Each Account now includes an explicit currency field (e.g., "USD" or "BTC")
to enforce that each account holds only one type of asset.
Accounts include:
  - Bank (USD)
  - Wallet (BTC)
  - ExchangeUSD (USD)
  - ExchangeBTC (BTC)

Relationships:
  - user: The User who owns this account.
  - transactions_from: Transactions where this account is debited.
  - transactions_to: Transactions where this account is credited.
"""

from enum import Enum
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

# Define AccountType enum for external use.
class AccountType(Enum):
    Bank = "Bank"
    Wallet = "Wallet"
    ExchangeUSD = "ExchangeUSD"
    ExchangeBTC = "ExchangeBTC"

class Account(Base):
    __tablename__ = "accounts"
    
    # Primary key.
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key linking to the owning user.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # The account name, e.g., "Bank", "Wallet", "ExchangeUSD", "ExchangeBTC".
    name = Column(String, unique=True, nullable=False)
    
    # Explicit currency field: "USD" or "BTC".
    currency = Column(String, nullable=False, default="USD")
    
    # Relationship to the owning User.
    user = relationship("User", back_populates="accounts")
    
    # Relationships to transactions (for debit and credit sides).
    transactions_from = relationship("Transaction", foreign_keys="[Transaction.from_account_id]")
    transactions_to   = relationship("Transaction", foreign_keys="[Transaction.to_account_id]")

    def __repr__(self):
        return f"<Account(name={self.name}, currency={self.currency})>"
