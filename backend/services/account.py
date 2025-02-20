"""
backend/services/account.py

Refactored to handle user_id in the AccountCreate schema.
Each Account is linked to exactly one User via user_id.
"""

from sqlalchemy.orm import Session
from backend.models.account import Account
from backend.schemas.account import AccountCreate, AccountUpdate

def get_all_accounts(db: Session):
    """Retrieve all accounts from the DB."""
    return db.query(Account).all()

def get_account_by_id(account_id: int, db: Session):
    """Retrieve a single account by its ID, or None if not found."""
    return db.query(Account).filter(Account.id == account_id).first()

def create_account(account_data: AccountCreate, db: Session):
    """
    Create a new account using data from AccountCreate.
    The DB schema requires user_id, name, and currency to be non-null.

    account_data.user_id must point to an existing user, or you'll get an FK error.
    """
    new_account = Account(
        user_id=account_data.user_id,  # Now we set user_id from the schema
        name=account_data.name,
        currency=account_data.currency,
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account

def update_account(account_id: int, account_data: AccountUpdate, db: Session):
    """
    Update an existing account's name/currency (if provided).
    If you need to allow changing user_id, add that logic here.
    """
    account = get_account_by_id(account_id, db)
    if not account:
        return None

    if account_data.name is not None:
        account.name = account_data.name
    if account_data.currency is not None:
        account.currency = account_data.currency
    # If you decide to allow user_id changes:
    # if account_data.user_id is not None:
    #     account.user_id = account_data.user_id

    db.commit()
    db.refresh(account)
    return account

def delete_account(account_id: int, db: Session):
    """
    Delete an account by its ID.
    Real systems often archive accounts instead of deleting them,
    especially if they have transaction history.
    """
    account = get_account_by_id(account_id, db)
    if not account:
        return False

    db.delete(account)
    db.commit()
    return True
