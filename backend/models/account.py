"""
backend/models/account.py

This module defines the Account model for BitcoinTX—a Bitcoin-only portfolio
tracker and transaction management application.

Key Features:
  - Supports different account types via an enumeration (Bank, Wallet, Exchange).
  - Stores balances in both USD and BTC for flexibility.
  - Establishes relationships with the User and Transaction models.
  - Includes helper methods to update account balances.

Note:
  Although BitcoinTX is designed as a one-user application, the model allows
  that user to have multiple accounts (e.g., a bank account for fiat funds,
  a wallet for BTC, and an exchange account for trading). This design supports
  clear separation of funds and provides flexibility for future enhancements.
"""

from sqlalchemy import Column, Integer, Float, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base
import enum

# --- Enumerations for Account Handling ---

class AccountType(enum.Enum):
    """
    Enum representing the type of account.

    Allowed values:
      - Bank: Represents a bank account that holds fiat currency (USD).
      - Wallet: Represents a cryptocurrency wallet that holds Bitcoin (BTC).
      - Exchange: Represents an exchange account that can hold both fiat and BTC.
    """
    Bank = "Bank"
    Wallet = "Wallet"
    Exchange = "Exchange"


# --- Account Model ---

class Account(Base):
    """
    SQLAlchemy ORM model representing an account in BitcoinTX.

    Attributes:
      id (int): Unique identifier for the account.
      user_id (int): Foreign key referencing the single user's ID.
      type (AccountType): The type of the account (Bank, Wallet, Exchange).
      balance_usd (float): The current balance in US Dollars.
      balance_btc (float): The current balance in Bitcoin.
      
    Relationships:
      - user: A relationship linking this account to the User model.
      - transactions: A relationship linking this account to its Transaction records.
      
    Methods:
      update_balance: Adjusts the USD and BTC balances by specified amounts.
    """
    __tablename__ = 'accounts'

    # Primary key: Unique identifier for the account.
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key: References the unique ID of the user (BitcoinTX is a one-user app).
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Account type: Uses the AccountType enum to distinguish between Bank, Wallet, and Exchange.
    type = Column(SAEnum(AccountType), nullable=False)
    
    # Balances: Store the fiat and cryptocurrency balances.
    balance_usd = Column(Float, default=0.0, nullable=False)
    balance_btc = Column(Float, default=0.0, nullable=False)

    # Relationships:
    # - 'user' links to the User model; back_populates ensures two-way access.
    user = relationship("User", back_populates="accounts")
    # - 'transactions' links to all Transaction records associated with this account.
    transactions = relationship("Transaction", back_populates="account")

    def update_balance(self, amount_usd: float = 0.0, amount_btc: float = 0.0):
        """
        Update the account's balances by adding the specified amounts.

        Args:
            amount_usd (float): The amount to adjust the USD balance (can be positive or negative).
            amount_btc (float): The amount to adjust the BTC balance (can be positive or negative).

        This method allows for both deposits and withdrawals (or fee adjustments)
        by applying the respective delta values.
        """
        self.balance_usd += amount_usd
        self.balance_btc += amount_btc

    def __repr__(self):
        """
        Return a string representation of the Account instance for debugging purposes.
        """
        return (
            f"<Account(id={self.id}, user_id={self.user_id}, type={self.type}, "
            f"balance_usd={self.balance_usd}, balance_btc={self.balance_btc})>"
        )
