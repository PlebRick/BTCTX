# backend/models/__init__.py

# This __init__.py file ensures that models and database components are available
# for import throughout the backend application. It helps keep the codebase modular
# and consistent by centralizing model imports.

from .user import User               # Import the User model from models/user.py
from .account import Account, AccountType  # Import the Account model and AccountType enum from models/account.py

# Only import 'Transaction' now. We have removed TransactionSource or other old enums,
# since our final refactor stores 'source' and 'type' as simple string fields.
from .transaction import Transaction

from backend.database import Base     # Import the SQLAlchemy Base for model inheritance
