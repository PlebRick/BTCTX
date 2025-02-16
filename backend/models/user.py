"""
backend/models/user.py

Refactored in the context of the new double-entry system.
No significant changes were required here, since:
  - The User model itself does not reference Transaction or account_id directly.
  - The Accounts relationship remains valid in double-entry; each Account can now have
    transactions_from and transactions_to, but that's handled in Account's model.

We merely add comments indicating how User relates to the updated Account structure.
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from passlib.context import CryptContext

from backend.database import Base

# --- Password Hashing Context ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    """
    Represents a user of the BitcoinTX application.

    Even though the app is primarily single-user, we design this model so it can handle
    multiple users if needed in the future. Each User can have multiple Account records
    (like Bank, Wallet, ExchangeUSD, ExchangeBTC, etc.).
    """
    __tablename__ = 'users'

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Unique username
    username = Column(String(255), unique=True, nullable=False)

    # Bcrypt-hashed password
    password_hash = Column(String(255), nullable=False)

    # Relationship to Account
    # 'accounts' is a list of Account objects that belong to this user.
    # In double-entry, each Account can have transactions_from and transactions_to
    # referencing the Transaction model, but that doesn't require changes here.
    accounts = relationship("Account", back_populates="user")

    def set_password(self, password: str):
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
