"""
backend/models/user.py

This module defines the User model for BitcoinTX—a Bitcoin-only portfolio tracker
and transaction management application.

BitcoinTX is designed as a one-user application, so typically only a single user record
will exist. However, the model is built using standard practices to allow for future
extensions or changes if needed.

Key Features:
  - Stores a unique user ID, username, and a hashed password.
  - Uses passlib to securely hash and verify passwords.
  - Establishes a one-to-many relationship with the Account model (each user can have
    multiple accounts, such as a bank account, wallet, and exchange account).
  - Provides helper methods for setting and verifying passwords.
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from backend.database import Base
from passlib.context import CryptContext

# --- Password Hashing Context ---
# The CryptContext is configured to use bcrypt for hashing passwords.
# This context allows you to hash passwords securely and verify them later.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- User Model ---
class User(Base):
    __tablename__ = 'users'

    # --- Columns ---
    id = Column(Integer, primary_key=True, index=True)  
    # 'id' is the unique identifier for the user.

    username = Column(String(255), unique=True, nullable=False)  
    # 'username' is the unique login identifier.
    
    password_hash = Column(String(255), nullable=False)  
    # 'password_hash' stores the securely hashed password.

    # --- Relationships ---
    accounts = relationship("Account", back_populates="user")
    # The 'accounts' relationship links this user to one or more Account records.
    # Even though BitcoinTX is a one-user application, this relationship allows the user
    # to manage multiple accounts (e.g., Bank, Wallet, Exchange).

    # --- Helper Methods ---
    
    def set_password(self, password: str):
        """
        Hash and set the user's password.

        This method takes a plain-text password, hashes it using bcrypt (via passlib),
        and stores the resulting hash in the password_hash column.

        Args:
            password (str): The plain-text password to be hashed.
        """
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """
        Verify the provided plain-text password against the stored hash.

        Args:
            password (str): The plain-text password to verify.

        Returns:
            bool: True if the password matches the stored hash; otherwise, False.
        """
        return pwd_context.verify(password, self.password_hash)

    def __repr__(self) -> str:
        """
        Provide a string representation of the User instance for debugging purposes.

        Returns:
            str: A string representation of the user, including id and username.
        """
        return f"<User(id={self.id}, username={self.username})>"
