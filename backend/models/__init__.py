# This __init__.py file ensures that models and database components are available
# for import throughout the backend application. This helps keep the codebase modular
# and consistent by centralizing model imports.

from .user import User            # Import the User model from models/user.py
from .account import Account, AccountType  # Import the Account model and AccountType enum from models/account.py
from .transaction import (        # Import the Transaction model and related enums from models/transaction.py
    Transaction, 
    TransactionType, 
    TransactionPurpose, 
    TransactionSource
)
from backend.database import Base       # Import the SQLAlchemy Base for model inheritance