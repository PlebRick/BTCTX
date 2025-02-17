from __future__ import annotations
from typing import List, TYPE_CHECKING
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from passlib.context import CryptContext
from backend.database import Base

# Conditionally import Account for type checking.
if TYPE_CHECKING:
    from backend.models.account import Account

# --- Password Hashing Context ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    """
    Represents a user of the BitcoinTX application.

    Even though the app is primarily single-user, this model is designed to handle
    multiple users if needed. Each User can have multiple Account records (e.g.,
    Bank, Wallet, ExchangeUSD, ExchangeBTC).
    """
    __tablename__ = 'users'

    # Primary key.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Unique username.
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Bcrypt-hashed password.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationship to Account.
    # 'accounts' is a list of Account objects that belong to this user.
    accounts: Mapped[List[Account]] = relationship("Account", back_populates="user")

    def set_password(self, password: str) -> None:
        """
        Hash and store the user's password using passlib (bcrypt).
        """
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """
        Verify a plain-text password against the stored hash.
        """
        return pwd_context.verify(password, self.password_hash)

    def __repr__(self) -> str:
        """
        Debug-friendly string representation of this User instance.
        """
        return f"<User(id={self.id}, username={self.username})>"
