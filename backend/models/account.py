# account.py
# Defines the Account model for BitcoinTX, representing different account types (e.g., Bank, Wallet, Exchange).
# This model handles relationships with the User and Transaction models.

from sqlalchemy import Column, Integer, String, Float, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base
import enum

# --- Enums for account handling ---
class AccountType(enum.Enum):
    """
    Enum representing the type of account (e.g., Bank, Wallet, Exchange).
    """
    Bank = "Bank"
    Wallet = "Wallet"
    Exchange = "Exchange"

# --- Account Model ---
class Account(Base):
    __tablename__ = 'accounts'

    # --- Columns ---
    id = Column(Integer, primary_key=True, index=True)                    # Unique identifier for the account
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)     # Reference to the associated user
    type = Column(SAEnum(AccountType), nullable=False)                    # Account type (Bank, Wallet, Exchange)
    balance_usd = Column(Float, default=0.0, nullable=False)              # Account balance in USD
    balance_btc = Column(Float, default=0.0, nullable=False)              # Account balance in BTC

    # --- Relationships ---
    user = relationship("User", back_populates="accounts")                # Relationship to the User model
    transactions = relationship("Transaction", back_populates="account")  # Relationship to Transaction model

    # --- Methods for Account Logic ---
    def update_balance(self, amount_usd: float = 0.0, amount_btc: float = 0.0):
        """
        Updates the account's balances.

        Args:
            amount_usd (float): The amount to adjust in USD.
            amount_btc (float): The amount to adjust in BTC.
        """
        self.balance_usd += amount_usd
        self.balance_btc += amount_btc