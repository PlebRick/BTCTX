# user.py
# Defines the User model, which handles authentication and associations with accounts.

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from backend.database import Base
from passlib.context import CryptContext

# --- Password Hashing Context ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- User Model ---
class User(Base):
    __tablename__ = 'users'

    # --- Columns ---
    id = Column(Integer, primary_key=True, index=True)     # Unique identifier for the user
    username = Column(String(255), unique=True, nullable=False)  # Unique username for login
    password_hash = Column(String(255), nullable=False)    # Hashed password

    # --- Relationships ---
    accounts = relationship("Account", back_populates="user")  # One-to-many relationship with Account

    # --- Helper Methods ---
    
    def set_password(self, password: str):
        """
        Hashes and sets the user's password.
        
        Args:
            password (str): The plain-text password to hash.
        """
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """
        Verifies a given password against the stored password hash.
        
        Args:
            password (str): The plain-text password to verify.
        
        Returns:
            bool: True if the password matches, False otherwise.
        """
        return pwd_context.verify(password, self.password_hash)