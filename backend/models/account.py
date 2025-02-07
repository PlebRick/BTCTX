"""
models/account.py

Defines the Account model for BitcoinTX. We've updated it to:
  - Use DECIMAL(12,2) for USD balances.
  - Use DECIMAL(16,8) for BTC balances.

SQLite doesn't strictly enforce these precision rules, but using DECIMAL in SQLAlchemy
helps clarify our financial intentions, avoids floating-point round-off issues in Python,
and makes future migrations to stricter databases (like Postgres) seamless.
"""

from sqlalchemy import Column, Integer, ForeignKey, DECIMAL, Enum as SAEnum, Float
from sqlalchemy.orm import relationship
from backend.database import Base
import enum

class AccountType(enum.Enum):
    """
    Enum representing the type of account.
    Allowed values:
      - Bank
      - Wallet
      - Exchange
    """
    Bank = "Bank"
    Wallet = "Wallet"
    Exchange = "Exchange"

class Account(Base):
    """
    SQLAlchemy ORM model representing an account in BitcoinTX.

    Changes for DECIMAL Precision:
      - balance_usd: DECIMAL(12, 2)
      - balance_btc: DECIMAL(16, 8)

    Even though SQLite won't strictly enforce these,
    it signals to SQLAlchemy and future DBs that we want exact decimal math.
    """
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(SAEnum(AccountType), nullable=False)

    # Use DECIMAL(12,2) for USD, DECIMAL(16,8) for BTC
    balance_usd = Column(DECIMAL(12, 2), default=0, nullable=False)
    balance_btc = Column(DECIMAL(16, 8), default=0, nullable=False)

    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")

    def update_balance(self, amount_usd: float = 0.0, amount_btc: float = 0.0):
        """
        Adjust this account's balances by the given amounts.
        If negative, it's effectively a withdrawal; if positive, it's a deposit.
        Using DECIMAL in the database helps avoid floating-point rounding errors.
        """
        # Convert to float or decimal as needed. Typically you'd handle decimal.Decimal carefully here.
        current_usd = float(self.balance_usd) if self.balance_usd else 0.0
        current_btc = float(self.balance_btc) if self.balance_btc else 0.0

        self.balance_usd = current_usd + amount_usd
        self.balance_btc = current_btc + amount_btc

    def __repr__(self):
        return (f"<Account(id={self.id}, user_id={self.user_id}, type={self.type}, "
                f"balance_usd={self.balance_usd}, balance_btc={self.balance_btc})>")
