"""
backend/services/account.py

Service functions to handle Account CRUD operations.
These functions interact with the Account model and are used by the API routes.
"""

from sqlalchemy.orm import Session
from backend.models.account import Account
from backend.schemas.account import AccountCreate, AccountUpdate

def get_all_accounts(db: Session):
    """Retrieve all accounts."""
    return db.query(Account).all()

def get_account_by_id(account_id: int, db: Session):
    """Retrieve a single account by its ID."""
    return db.query(Account).filter(Account.id == account_id).first()

def create_account(account_data: AccountCreate, db: Session):
    """Create a new account using provided data."""
    new_account = Account(
        name=account_data.name,
        currency=account_data.currency
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account

def update_account(account_id: int, account_data: AccountUpdate, db: Session):
    """Update an existing account's details."""
    account = get_account_by_id(account_id, db)
    if not account:
        return None
    if account_data.name is not None:
        account.name = account_data.name
    if account_data.currency is not None:
        account.currency = account_data.currency
    db.commit()
    db.refresh(account)
    return account

def delete_account(account_id: int, db: Session):
    """Delete an account by its ID."""
    account = get_account_by_id(account_id, db)
    if not account:
        return False
    db.delete(account)
    db.commit()
    return True
