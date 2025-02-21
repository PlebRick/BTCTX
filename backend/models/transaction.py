"""
backend/models/transaction.py

Updated to reintroduce `source` and `purpose` for deposits/withdrawals:
 - source: e.g., "Gift", "Income", "MyBTC"
 - purpose: e.g., "Spent", "Donation", "Lost"

We store them as SQLAlchemy Enums using the existing TransactionSource and
TransactionPurpose enums. Both are nullable so they can be omitted for
transaction types that don't require them (e.g., Transfer, Buy, Sell).
"""

import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Numeric,
    Boolean,
    ForeignKey,
    Enum as SAEnum  # <-- Added so we can store Python enums as SQL enums in the DB
)
from sqlalchemy.orm import relationship
from backend.database import Base

# -------------------------------------------------------------------
# Enums for transaction classification
# -------------------------------------------------------------------

class TransactionType(enum.Enum):
    """
    Used to classify the overall transaction nature:
      - Deposit, Withdrawal, Transfer, Buy, Sell
    """
    Deposit = "Deposit"
    Withdrawal = "Withdrawal"
    Transfer = "Transfer"
    Buy = "Buy"
    Sell = "Sell"


class TransactionPurpose(enum.Enum):
    """
    Used mainly for BTC withdrawals:
      - "N/A", "Spent", "Gift", "Donation", "Lost"
    """
    NA = "N/A"
    Spent = "Spent"
    Gift = "Gift"
    Donation = "Donation"
    Lost = "Lost"


class TransactionSource(enum.Enum):
    """
    Used mainly for BTC deposits:
      - "N/A", "MyBTC", "Gift", "Income", "Interest", "Reward"
    """
    NA = "N/A"
    MyBTC = "MyBTC"
    Gift = "Gift"
    Income = "Income"
    Interest = "Interest"
    Reward = "Reward"


# -------------------------------------------------------------------
# Transaction Model
# -------------------------------------------------------------------

class Transaction(Base):
    __tablename__ = "transactions"
    
    # ----------------------------
    # Primary key
    # ----------------------------
    id = Column(Integer, primary_key=True, index=True)
    
    # ----------------------------
    # Double-entry: from/to
    # ----------------------------
    from_account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=True,
        doc="Source account ID (debit side). For example, user wallet or external."
    )
    to_account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=True,
        doc="Destination account ID (credit side)."
    )
    
    # ----------------------------
    # Amount & Type
    # ----------------------------
    amount = Column(
        Numeric(precision=18, scale=8),
        nullable=False,
        doc="Main transaction amount (in the from_account's currency)."
    )
    type = Column(
        String,
        nullable=False,
        doc="Transaction type, e.g., 'Deposit', 'Withdrawal', 'Transfer', 'Buy', 'Sell'."
    )
    
    # ----------------------------
    # Timestamp & Audit
    # ----------------------------
    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="Datetime the transaction occurred."
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="Record creation time (auto-set)."
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        doc="Time of last record update (auto-set)."
    )
    is_locked = Column(
        Boolean,
        default=False,
        doc="Prevents edits/deletion if True."
    )
    
    # ----------------------------
    # Grouping (optional)
    # ----------------------------
    group_id = Column(
        Integer,
        index=True,
        nullable=True,
        doc="Group ID to link multiple transaction rows if needed."
    )
    
    # ----------------------------
    # Tax fields (optional usage)
    # ----------------------------
    cost_basis_usd = Column(
        Numeric(precision=18, scale=2),
        nullable=True,
        doc="USD cost basis for acquired BTC (e.g., external deposit or buy)."
    )
    proceeds_usd = Column(
        Numeric(precision=18, scale=2),
        nullable=True,
        doc="USD proceeds for disposed BTC (e.g., sell)."
    )
    realized_gain_usd = Column(
        Numeric(precision=18, scale=2),
        nullable=True,
        doc="Realized gain/loss in USD if proceeds - cost_basis."
    )
    holding_period = Column(
        String,
        nullable=True,
        doc="Holding period classification: 'SHORT' or 'LONG'."
    )
    
    # ----------------------------
    # Fee (amount, currency)
    # ----------------------------
    fee_amount = Column(
        Numeric(precision=18, scale=8),
        nullable=True,
        doc="Transaction fee amount, in fee_currency units."
    )
    fee_currency = Column(
        String,
        nullable=True,
        doc="Currency of the fee (e.g. 'USD' or 'BTC')."
    )
    
    # ----------------------------
    # External reference
    # ----------------------------
    external_ref = Column(
        String,
        nullable=True,
        doc="Any external reference or identifier (e.g. exchange name, address)."
    )
    
    # ----------------------------
    # Reintroduced Fields
    # ----------------------------
    source = Column(
        SAEnum(TransactionSource),
        nullable=True,
        doc=(
            "Deposit source: e.g. 'Gift', 'Income'. "
            "Primarily relevant if type='Deposit' and currency=BTC."
        )
    )
    purpose = Column(
        SAEnum(TransactionPurpose),
        nullable=True,
        doc=(
            "Withdrawal purpose: e.g. 'Spent', 'Donation'. "
            "Primarily relevant if type='Withdrawal' and currency=BTC."
        )
    )
    
    # ----------------------------
    # Relationships
    # ----------------------------
    from_account = relationship(
        "Account",
        foreign_keys=[from_account_id]
    )
    to_account = relationship(
        "Account",
        foreign_keys=[to_account_id]
    )
    
    def __repr__(self):
        return (
            f"<Transaction(id={self.id}, type={self.type}, amount={self.amount}, "
            f"from={self.from_account_id}, to={self.to_account_id}, source={self.source}, "
            f"purpose={self.purpose}, group_id={self.group_id})>"
        )
