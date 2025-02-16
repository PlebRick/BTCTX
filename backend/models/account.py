"""
models/account.py

Refactored for a double-entry approach:
  - Removed the single 'transactions' relationship to Transaction,
    since now each transaction has from_account_id and to_account_id.
  - Added relationships 'transactions_from' and 'transactions_to' to
    reference Transaction records where this account is the source or target.
  - Introduced two new enum values for AccountType:
    - ExchangeUSD
    - ExchangeBTC
    to differentiate them in the DB if you prefer that approach.
  - Alternatively, you could keep one 'Exchange' type and add a 'currency' column
    to reflect whether it's a BTC or USD sub-account. See note below for details.
"""

import enum
from sqlalchemy import Column, Integer, ForeignKey, DECIMAL, Enum as SAEnum
from sqlalchemy.orm import relationship
from backend.database import Base

class AccountType(enum.Enum):
    """
    Enum representing the type of account.

    Modified to separate Exchange accounts for USD vs BTC if desired:
      - Bank
      - Wallet
      - ExchangeUSD
      - ExchangeBTC

    If you prefer to keep a single 'Exchange' type, revert to 'Exchange'
    and introduce a separate column, e.g. 'currency = Column(String(3))'.
    """
    Bank = "Bank"
    Wallet = "Wallet"
    ExchangeUSD = "ExchangeUSD"
    ExchangeBTC = "ExchangeBTC"

class Account(Base):
    """
    SQLAlchemy ORM model representing an account in BitcoinTX.

    Key Changes:
      1. We replaced 'transactions' relationship with two relationships:
         transactions_from, transactions_to,
         corresponding to from_account_id and to_account_id in Transaction.
      2. Potentially changed the AccountType to add 'ExchangeUSD' and 'ExchangeBTC'
         if you want them as distinct types in DB.
      3. The decimal fields for balance_usd and balance_btc remain.
      4. The update_balance() method is unchanged except for doc notes.

    This allows:
      - A 'Bank' type account with a USD balance.
      - A 'Wallet' type account with a BTC balance.
      - 'ExchangeUSD' and 'ExchangeBTC' to separate the exchange's USD and BTC sides,
        so we can do double-entry trades by moving from ExchangeUSD to ExchangeBTC, etc.
    """

    __tablename__ = 'accounts'

    # ----------------------
    #   Primary Key
    # ----------------------
    id = Column(Integer, primary_key=True, index=True)

    # ----------------------
    #   Foreign Keys
    # ----------------------
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # ----------------------
    #   Type & Balances
    # ----------------------
    type = Column(SAEnum(AccountType), nullable=False)

    balance_usd = Column(DECIMAL(12, 2), default=0, nullable=False)
    balance_btc = Column(DECIMAL(16, 8), default=0, nullable=False)

    # ----------------------
    #   Relationships
    # ----------------------
    user = relationship("User", back_populates="accounts")

    # Instead of a single 'transactions' relationship, define two:
    transactions_from = relationship(
        "Transaction",
        foreign_keys="Transaction.from_account_id",
        back_populates="from_account"
    )
    transactions_to = relationship(
        "Transaction",
        foreign_keys="Transaction.to_account_id",
        back_populates="to_account"
    )

    def update_balance(self, amount_usd: float = 0.0, amount_btc: float = 0.0):
        """
        Adjust this account's balances by the given amounts.
        - Positive amounts represent a deposit/inflow.
        - Negative amounts represent a withdrawal/outflow.
        - DECIMAL(12,2) for USD and DECIMAL(16,8) for BTC help avoid float rounding issues.

        If you track 'type' as e.g. ExchangeUSD, it means this account
        is expected to have a positive or negative USD balance over time, but 0 BTC (ideally).
        Similarly, ExchangeBTC might track only BTC. It's not enforced at DB level,
        but recommended by usage patterns.
        """
        current_usd = float(self.balance_usd) if self.balance_usd else 0.0
        current_btc = float(self.balance_btc) if self.balance_btc else 0.0

        self.balance_usd = current_usd + amount_usd
        self.balance_btc = current_btc + amount_btc

    def __repr__(self):
        return (
            f"<Account(id={self.id}, user_id={self.user_id}, type={self.type}, "
            f"balance_usd={self.balance_usd}, balance_btc={self.balance_btc})>"
        )
