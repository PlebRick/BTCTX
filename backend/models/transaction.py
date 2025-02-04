# transaction.py
# Defines the Transaction model and related enums for transaction management in BitcoinTX.

from sqlalchemy import Column, Integer, Float, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base
import enum

# --- Enums for transaction handling ---
class TransactionType(enum.Enum):
    """
    Defines the type of transaction (e.g., Deposit, Withdrawal, Transfer, Buy, Sell).
    """
    Deposit = "Deposit"
    Withdrawal = "Withdrawal"
    Transfer = "Transfer"
    Buy = "Buy"
    Sell = "Sell"

class TransactionPurpose(enum.Enum):
    """
    Defines the purpose of BTC withdrawals for reporting and tax purposes.
    """
    NA = "N/A"
    Spent = "Spent"
    Gift = "Gift"
    Donation = "Donation"
    Lost = "Lost"

class TransactionSource(enum.Enum):
    """
    Defines the source of BTC deposits for categorization.
    """
    NA = "N/A"
    MyBTC = "My BTC"
    Gift = "Gift"
    Income = "Income"
    Interest = "Interest"
    Reward = "Reward"

# --- Transaction Model ---
class Transaction(Base):
    __tablename__ = 'transactions'

    # --- Columns ---
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)  # Reference to the associated account
    type = Column(SAEnum(TransactionType), nullable=False)                   # Type of transaction (Deposit, Buy, etc.)
    amount_usd = Column(Float, default=0.0, nullable=False)                  # Amount in USD (non-negative)
    amount_btc = Column(Float, default=0.0, nullable=False)                  # Amount in BTC (non-negative)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)    # Transaction timestamp
    purpose = Column(SAEnum(TransactionPurpose), nullable=True)              # Purpose for BTC withdrawals
    source = Column(SAEnum(TransactionSource), nullable=True)                # Source for BTC deposits

    # --- Relationships ---
    account = relationship("Account", back_populates="transactions")         # Relationship to the Account model