"""
models/transaction.py

Refactored to support a single-row double-entry design (Plan B):
  - Removed account_id in favor of from_account_id and to_account_id.
  - Each Transaction row now represents one user action (Deposit, Withdrawal, Transfer, Buy, Sell),
    with a 'from' side and a 'to' side.
  - The columns amount_usd and amount_btc remain for storing the currency amounts involved.
    For cross-currency (e.g., Buy), it's possible that from_account uses USD while to_account uses BTC.
  - cost_basis_usd and fee remain on the Transaction for consistency with prior usage.
  - is_locked still enforces a locking mechanism (discussed elsewhere).
  - We preserve enumerations for type, purpose, source.
  - Timestamps are still DateTime, defaulting to datetime.utcnow (treated as UTC).
"""

import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    Boolean,
    DECIMAL,
    Enum as SAEnum,
    ForeignKey
)
from sqlalchemy.orm import relationship
from backend.database import Base

# ----------------------
#     Enumerations
# ----------------------

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

# ----------------------
#     Transaction
# ----------------------

class Transaction(Base):
    """
    SQLAlchemy ORM model for a single transaction row in BitcoinTX,
    supporting Plan B for double-entry: a single row with 'from' and 'to' accounts.

    Key Changes vs. old design:
      1. Removed account_id (old single-account reference).
      2. Added from_account_id and to_account_id (both referencing the 'accounts' table).
      3. Kept amount_usd, amount_btc, fee, cost_basis_usd, etc. so minimal disruption to rest of code.
      4. Each transaction can represent:
         - Deposit (from_account_id=External, to_account_id=some user account),
         - Withdrawal (from_account_id=user account, to_account_id=External),
         - Transfer (from_account_id=user account A, to_account_id=user account B),
         - Buy (from_account_id=ExchangeUSD, to_account_id=ExchangeBTC),
         - Sell (inverse of Buy).
      5. is_locked remains for the transaction-locking logic.

    SQLAlchemy Notes:
      - from_account_id and to_account_id can be nullable=False, or you can allow them to be nullable
        if certain special cases (like purely external placeholders) appear. For minimal confusion,
        let's keep them non-nullable so every transaction has a distinct "from" and "to" side.

    Decimal Precision:
      - amount_usd: DECIMAL(12, 2)
      - amount_btc: DECIMAL(16, 8)
      - fee: DECIMAL(12, 2)
      - cost_basis_usd: DECIMAL(12, 2)
    """

    __tablename__ = 'transactions'

    # ----------------------
    #  Primary Key
    # ----------------------
    id = Column(Integer, primary_key=True, index=True)

    # ----------------------
    #  Accounts (New Fields)
    # ----------------------
    from_account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False,
                             doc="Which account funds are moving from.")
    to_account_id   = Column(Integer, ForeignKey('accounts.id'), nullable=False,
                             doc="Which account funds are moving to.")

    # ----------------------
    #  Transaction Type
    # ----------------------
    type = Column(SAEnum(TransactionType), nullable=False, doc="Deposit, Withdrawal, Transfer, Buy, Sell")

    # ----------------------
    #  Currency Amounts
    # ----------------------
    amount_usd = Column(DECIMAL(12, 2), default=0, nullable=False,
                        doc="Amount of USD involved in this transaction (if any).")
    amount_btc = Column(DECIMAL(16, 8), default=0, nullable=False,
                        doc="Amount of BTC involved in this transaction (if any).")

    # ----------------------
    #  Additional Fields
    # ----------------------
    cost_basis_usd = Column(DECIMAL(12, 2), nullable=True,
                            doc="Optional cost basis in USD for BTC acquisitions (e.g. when depositing external BTC).")
    fee = Column(DECIMAL(12, 2), nullable=True,
                 doc="Transaction fee in USD (e.g. a trading fee or withdrawal fee).")

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False,
                       doc="Creation timestamp. Defaults to UTC at insertion time.")
    purpose   = Column(SAEnum(TransactionPurpose), nullable=True,
                       doc="Purpose (mostly relevant for withdrawals).")
    source    = Column(SAEnum(TransactionSource), nullable=True,
                       doc="Source (mostly relevant for deposits).")
    is_locked = Column(Boolean, default=False, nullable=False,
                       doc="Locking mechanism to prevent edits after year close.")

    # ----------------------
    #  Relationships
    # ----------------------
    # For convenience, we can define relationships to 'Account' for
    # from_account and to_account. The 'Account' model must have no
    # conflicting relationship names. We'll just define them here
    # if we want easy access to the actual objects:
    from_account = relationship(
        "Account",
        foreign_keys=[from_account_id],
        back_populates="transactions_from"
    )
    to_account = relationship(
        "Account",
        foreign_keys=[to_account_id],
        back_populates="transactions_to"
    )

    def __repr__(self):
        return (
            f"<Transaction(id={self.id}, "
            f"from_account_id={self.from_account_id}, to_account_id={self.to_account_id}, "
            f"type={self.type}, amount_usd={self.amount_usd}, amount_btc={self.amount_btc}, "
            f"fee={self.fee}, cost_basis_usd={self.cost_basis_usd}, "
            f"timestamp={self.timestamp}, is_locked={self.is_locked}, "
            f"purpose={self.purpose}, source={self.source})>"
        )
