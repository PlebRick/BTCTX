import os
print("PYTHONPATH:", os.getenv('PYTHONPATH'))

import pytest
from backend.models.user import User
from backend.models.account import Account
from backend.models.transaction import Transaction
from backend.database import Base, engine

print("All backend imports are working!")

def test_user_model():
    user = User(name="Test User")
    assert user.name == "Test User"

def test_account_model():
    account = Account(name="Test Account")
    assert account.name == "Test Account"

def test_transaction_model():
    transaction = Transaction(amount=100)
    assert transaction.amount == 100