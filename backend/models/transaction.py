"""
backend/models/transaction.py

This module defines the Transaction model for BitcoinTX.
Each Transaction now records a double‐entry: it has both a from_account_id (source)
and a to_account_id (destination). Additional fields have been added for:
  - Grouping related entries (group_id) to link debit/credit pairs or track FIFO lots.
  - Audit: created_at and updated_at timestamps.
  - Tax reporting: cost_basis_usd, proceeds_usd, realized_gain_usd, and holding_period.
  - Fee tracking: fee_amount and fee_currency.
  - External reference: external_ref to note external sources/destinations.

Below, we define enums for transaction categorization.
"""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

# Enum for transaction types.
class TransactionType(enum.Enum):
    Deposit = "Deposit"
    Withdrawal = "Withdrawal"
    Transfer = "Transfer"
    Buy = "Buy"
    Sell = "Sell"

# Enum for transaction purpose (used mainly for withdrawals).
class TransactionPurpose(enum.Enum):
    NA = "N/A"
    Spent = "Spent"
    Gift = "Gift"
    Donation = "Donation"
    Lost = "Lost"

# Enum for transaction source (used mainly for deposits).
class TransactionSource(enum.Enum):
    NA = "N/A"
    MyBTC = "My BTC"
    Gift = "Gift"
    Income = "Income"
    Interest = "Interest"
    Reward = "Reward"

class Transaction(Base):
    __tablename__ = "transactions"
    
    # Primary key.
    id = Column(Integer, primary_key=True, index=True)
    
    # Double-entry fields: source and destination account IDs.
    from_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True,
                               doc="Source account ID (debit)")
    to_account_id   = Column(Integer, ForeignKey("accounts.id"), nullable=True,
                               doc="Destination account ID (credit)")
    
    # Transaction amount (interpreted in context of the account's currency).
    amount = Column(Numeric(precision=18, scale=8), nullable=False,
                    doc="Transaction amount")
    
    # Transaction type stored as a string. Although we defined the enum above,
    # we store its value (e.g., "Deposit", "Withdrawal", etc.) in the database.
    type = Column(String, nullable=False, doc="Transaction type")
    
    # Timestamp when the transaction occurred.
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False,
                       doc="Transaction timestamp")
    
    # Audit fields.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False,
                        doc="Record creation time")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False,
                        doc="Record update time")
    
    # Lock flag to prevent further edits.
    is_locked = Column(Boolean, default=False, doc="Lock flag to prevent edits")
    
    # Group identifier to link related entries (for transfers or trade pairs).
    group_id = Column(Integer, index=True, nullable=True,
                      doc="Identifier to link related entries")
    
    # Tax fields.
    cost_basis_usd = Column(Numeric(precision=18, scale=2), nullable=True,
                            doc="USD cost basis for acquired BTC")
    proceeds_usd   = Column(Numeric(precision=18, scale=2), nullable=True,
                            doc="USD proceeds for disposed BTC")
    realized_gain_usd = Column(Numeric(precision=18, scale=2), nullable=True,
                               doc="Realized gain/loss in USD")
    holding_period = Column(String, nullable=True,
                            doc="Holding period: 'SHORT' or 'LONG'")
    
    # Fee fields.
    fee_amount = Column(Numeric(precision=18, scale=8), nullable=True,
                        doc="Transaction fee amount")
    fee_currency = Column(String, nullable=True,
                          doc="Currency of the fee (e.g., 'USD' or 'BTC')")
    
    # External reference to note external source/destination (e.g., exchange name, wallet address).
    external_ref = Column(String, nullable=True,
                          doc="Reference for external source/destination")
    
    # Relationships to Account for convenience.
    from_account = relationship("Account", foreign_keys=[from_account_id])
    to_account   = relationship("Account", foreign_keys=[to_account_id])
    
    def __repr__(self):
        return (f"<Transaction(id={self.id}, type={self.type}, amount={self.amount}, "
                f"from={self.from_account_id}, to={self.to_account_id}, group_id={self.group_id})>")
