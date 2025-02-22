"""
backend/models/user.py

Represents a user of the BitcoinTX application. Even if this is mostly single-user,
the design supports multiple users. Each user can own multiple Accounts,
and each Account can participate in many LedgerEntry lines or single-row Transactions.
No further changes needed for double-entry, but we confirm the layout is correct.
"""

from __future__ import annotations
from typing import List, TYPE_CHECKING
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from passlib.context import CryptContext
from backend.database import Base

if TYPE_CHECKING:
    from backend.models.account import Account

# Setup passlib for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    """
    The main user table. Each user has:
      - An ID (PK)
      - A unique username
      - A hashed password
      - A list of accounts (bank, wallet, fees, etc.)
    """

    __tablename__ = 'users'

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Unique username for login
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Bcrypt-hashed password storage
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationship: a user can have many accounts
    accounts: Mapped[List[Account]] = relationship(
        "Account",
        back_populates="user",
        doc="All accounts owned by this user."
    )

    def set_password(self, password: str) -> None:
        """
        Hash and store the user's password using passlib (bcrypt).
        The field 'password_hash' holds the result.
        """
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """
        Verify a plain-text password against the stored hash.
        """
        return pwd_context.verify(password, self.password_hash)

    def __repr__(self) -> str:
        """
        String representation for debugging, showing user ID and username.
        """
        return f"<User(id={self.id}, username={self.username})>"
    