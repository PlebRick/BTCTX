"""
transaction.py

This module defines the Transaction model and related enumerations for BitcoinTX,
a Bitcoin-only portfolio tracker and transaction manager.

BitcoinTX supports various transaction types, including:
  - Deposit
  - Withdrawal
  - Transfer
  - Buy
  - Sell

For each transaction, the model records:
  - The unique identifier (id).
  - The associated account (account_id) as a foreign key.
  - The type of transaction (using the TransactionType enum).
  - The transaction amounts in both USD and BTC.
  - A timestamp for when the transaction occurred.
  - Additional information:
      * For withdrawals, the purpose (using TransactionPurpose).
      * For deposits, the source (using TransactionSource).
  - Optional fee details: fee_currency and fee_amount.

These fee details are later assembled into a nested object in the Pydantic schema
for transaction output. Ensure that any changes here are reflected in the
corresponding schemas (see backend/schemas/transaction.py).

This module uses SQLAlchemy for ORM mapping. All models inherit from the Base
class defined in backend/database.py.
"""

from sqlalchemy import Column, Integer, Float, DateTime, String, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base
import enum

# --- Enumerations for Transaction Handling ---

class TransactionType(enum.Enum):
    """
    Enum for the type of transaction.

    Allowed values:
      - Deposit: Adding funds to an account.
      - Withdrawal: Removing funds from an account.
      - Transfer: Moving funds between accounts.
      - Buy: Exchanging USD for BTC (in an exchange account).
      - Sell: Exchanging BTC for USD (in an exchange account).
    """
    Deposit = "Deposit"
    Withdrawal = "Withdrawal"
    Transfer = "Transfer"
    Buy = "Buy"
    Sell = "Sell"


class TransactionPurpose(enum.Enum):
    """
    Enum for the purpose of a withdrawal transaction.

    This is used for tax reporting and tracking the nature of the transaction.
    Allowed values:
      - NA: Not applicable.
      - Spent: Funds were spent.
      - Gift: Funds were given as a gift.
      - Donation: Funds were donated.
      - Lost: Funds were lost.
    """
    NA = "N/A"
    Spent = "Spent"
    Gift = "Gift"
    Donation = "Donation"
    Lost = "Lost"


class TransactionSource(enum.Enum):
    """
    Enum for the source of a deposit transaction.

    This categorizes the origin of funds. Allowed values:
      - NA: Not applicable.
      - MyBTC: Funds coming from the user's own Bitcoin.
      - Gift: Funds received as a gift.
      - Income: Funds received as income.
      - Interest: Funds received as interest.
      - Reward: Funds received as a reward.
    """
    NA = "N/A"
    MyBTC = "My BTC"
    Gift = "Gift"
    Income = "Income"
    Interest = "Interest"
    Reward = "Reward"


# --- Transaction Model ---

class Transaction(Base):
    """
    SQLAlchemy ORM model representing a transaction in BitcoinTX.

    Attributes:
      id (int): Primary key; unique identifier for each transaction.
      account_id (int): Foreign key referencing the associated account in the accounts table.
      type (TransactionType): Type of transaction (Deposit, Withdrawal, Transfer, Buy, Sell).
      amount_usd (float): Transaction amount in US Dollars.
      amount_btc (float): Transaction amount in Bitcoin.
      timestamp (datetime): When the transaction occurred (defaults to the current UTC time).
      purpose (Optional[TransactionPurpose]): For withdrawals, the purpose (e.g., Spent, Gift).
      source (Optional[TransactionSource]): For deposits, the source (e.g., Income, Gift).
      fee_currency (Optional[str]): The currency for any transaction fee (e.g., USD, BTC).
      fee_amount (Optional[float]): The fee amount.
      account (Relationship): A relationship linking this transaction to an Account model.
    """

    __tablename__ = 'transactions'

    # Primary key column: Unique transaction ID.
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key linking to the account associated with this transaction.
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    
    # Transaction type (e.g., Deposit, Withdrawal, etc.) stored as an enumeration.
    type = Column(SAEnum(TransactionType), nullable=False)
    
    # Transaction amounts: stored in both USD and BTC for flexibility.
    amount_usd = Column(Float, default=0.0, nullable=False)
    amount_btc = Column(Float, default=0.0, nullable=False)
    
    # Timestamp for when the transaction occurred.
    # Defaults to the current UTC time when a transaction is created.
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # For withdrawal transactions: records the purpose (e.g., Spent, Gift).
    purpose = Column(SAEnum(TransactionPurpose), nullable=True)
    
    # For deposit transactions: records the source (e.g., Income, Gift).
    source = Column(SAEnum(TransactionSource), nullable=True)
    
    # Fee details: stored in two separate columns.
    # fee_currency stores the currency of the fee (e.g., USD, BTC).
    fee_currency = Column(String, nullable=True)
    # fee_amount stores the numerical fee value.
    fee_amount = Column(Float, nullable=True)
    
    # Relationship to the Account model.
    # This allows easy navigation from a transaction to its associated account.
    account = relationship("Account", back_populates="transactions")

    def __repr__(self):
        """
        Provide a string representation of the Transaction instance.
        """
        return (
            f"<Transaction(id={self.id}, account_id={self.account_id}, type={self.type}, "
            f"amount_usd={self.amount_usd}, amount_btc={self.amount_btc}, timestamp={self.timestamp}, "
            f"purpose={self.purpose}, source={self.source}, fee_currency={self.fee_currency}, fee_amount={self.fee_amount})>"
        )
