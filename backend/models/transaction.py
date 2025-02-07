"""
models/transaction.py

Defines the Transaction model and related enumerations for BitcoinTX.
We've updated it to:
  - Use DECIMAL(12,2) for USD amounts and DECIMAL(16,8) for BTC amounts.
  - Preserve 'is_locked', 'cost_basis_usd', 'fee', enumerations, etc.
  - Store timestamps with a default of datetime.utcnow (treated as UTC).
"""

import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    String,
    Boolean,
    DECIMAL,
    Enum as SAEnum,
    ForeignKey
)
from sqlalchemy.orm import relationship
from backend.database import Base

class TransactionType(enum.Enum):
    """
    Enum for the type of transaction:
      - Deposit
      - Withdrawal
      - Transfer
      - Buy
      - Sell
    """
    Deposit = "Deposit"
    Withdrawal = "Withdrawal"
    Transfer = "Transfer"
    Buy = "Buy"
    Sell = "Sell"

class TransactionPurpose(enum.Enum):
    """
    Enum for the purpose of a withdrawal:
      - "N/A"
      - "Spent"
      - "Gift"
      - "Donation"
      - "Lost"
    """
    NA = "N/A"
    Spent = "Spent"
    Gift = "Gift"
    Donation = "Donation"
    Lost = "Lost"

class TransactionSource(enum.Enum):
    """
    Enum for the source of a deposit:
      - "N/A"
      - "My BTC"
      - "Gift"
      - "Income"
      - "Interest"
      - "Reward"
    """
    NA = "N/A"
    MyBTC = "My BTC"
    Gift = "Gift"
    Income = "Income"
    Interest = "Interest"
    Reward = "Reward"

class Transaction(Base):
    """
    SQLAlchemy ORM model for transactions in BitcoinTX.

    Changes for DECIMAL Precision:
      - amount_usd: DECIMAL(12,2)
      - amount_btc: DECIMAL(16,8)
      - fee: DECIMAL(12,2)
      - cost_basis_usd: DECIMAL(12,2)
      - is_locked remains a boolean placeholder for our locking mechanism.
    """

    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)

    type = Column(SAEnum(TransactionType), nullable=False)
    
    # Use DECIMAL(12,2) for USD, DECIMAL(16,8) for BTC
    amount_usd = Column(DECIMAL(12, 2), default=0, nullable=False)
    amount_btc = Column(DECIMAL(16, 8), default=0, nullable=False)

    # cost_basis_usd: cost basis for BTC deposits (optional for other types)
    cost_basis_usd = Column(DECIMAL(12, 2), nullable=True)

    # Single fee column in USD
    fee = Column(DECIMAL(12, 2), nullable=True)

    # Timestamps treated as UTC (though not forcibly converted)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    purpose = Column(SAEnum(TransactionPurpose), nullable=True)
    source = Column(SAEnum(TransactionSource), nullable=True)

    is_locked = Column(Boolean, default=False, nullable=False)

    account = relationship("Account", back_populates="transactions")

    def __repr__(self):
        return (
            f"<Transaction(id={self.id}, account_id={self.account_id}, type={self.type}, "
            f"amount_usd={self.amount_usd}, amount_btc={self.amount_btc}, timestamp={self.timestamp}, "
            f"fee={self.fee}, cost_basis_usd={self.cost_basis_usd}, is_locked={self.is_locked}, "
            f"purpose={self.purpose}, source={self.source})>"
        )
