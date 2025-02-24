"""
backend/models/account.py

Defines the Account model in a full double-entry environment. Each Account
can appear in many LedgerEntry records (credit/debit lines) referencing
'account_id'. We also keep references to any single-row usage in Transaction
via 'transactions_from' and 'transactions_to' for backward compatibility.

User => One-to-many => Account
Account => One-to-many => LedgerEntry (or part of single-row Transaction usage)

CHANGES:
- No need to reference LotDisposal here, since the disposal-level referencing
  is done at the Transaction/LedgerEntry level. We'll keep the existing
  ledger_entries relationship, which matches LedgerEntry.account.
"""

from enum import Enum
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

# Optional legacy enum if you want, or you can remove it.
class AccountType(Enum):
    """
    (LEGACY) If you once distinguished account types like "Bank", "Wallet",
    or "ExchangeUSD", etc. We now typically store just 'name' and 'currency'.
    """
    Bank = "Bank"
    Wallet = "Wallet"
    ExchangeUSD = "ExchangeUSD"
    ExchangeBTC = "ExchangeBTC"

class Account(Base):
    __tablename__ = "accounts"

    # ---------------------------------------------------------------------
    # Primary Key & Fields
    # ---------------------------------------------------------------------
    id = Column(Integer, primary_key=True, index=True)

    # Each Account belongs to one User, enforced by user_id (NOT NULL)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # A unique name, e.g. "Bank", "Wallet", "BTC Fees"
    name = Column(String, unique=True, nullable=False)

    # The currency: "USD" or "BTC" (extend if needed)
    currency = Column(String, nullable=False, default="USD")

    # ---------------------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------------------

    # The User that owns this account
    user = relationship(
        "User",
        back_populates="accounts",
        doc="The user that owns this account."
    )

    # If you still keep single-row references in Transaction:
    # (LEGACY) 'transactions_from' references where this account is the 'from' side
    transactions_from = relationship(
        "Transaction",
        foreign_keys="[Transaction.from_account_id]",
        doc="(LEGACY) Single-row approach: transactions listing this account as 'from'"
    )
    transactions_to = relationship(
        "Transaction",
        foreign_keys="[Transaction.to_account_id]",
        doc="(LEGACY) Single-row approach: transactions listing this account as 'to'"
    )

    # True double-entry lines: 'LedgerEntry' referencing account_id
    ledger_entries = relationship(
        "LedgerEntry",
        back_populates="account",
        cascade="all, delete-orphan",
        doc="All ledger lines (debit/credit) pointing to this account."
    )

    # ---------------------------------------------------------------------
    # Representation
    # ---------------------------------------------------------------------
    def __repr__(self):
        return (
            f"<Account(id={self.id}, user_id={self.user_id}, "
            f"name={self.name}, currency={self.currency})>"
        )