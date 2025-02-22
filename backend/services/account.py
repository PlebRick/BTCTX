"""
backend/services/account.py

Manages creation, update, deletion, and retrieval of Accounts.
In a double-entry environment, each Account can appear in many LedgerEntry lines
(e.g. for 'MAIN_IN', 'MAIN_OUT', 'FEE'). The user typically calls these endpoints
via account.py router.

We do NOT handle ledger logic here; that belongs to transaction or ledger services.
"""

from sqlalchemy.orm import Session
from backend.models.account import Account
from backend.schemas.account import AccountCreate, AccountUpdate

def get_all_accounts(db: Session):
    """
    Fetch all accounts in the system. 
    For a single-user scenario, you might filter by user_id if desired.
    """
    return db.query(Account).all()

def get_account_by_id(account_id: int, db: Session):
    """
    Return the Account with the specified ID, or None if it doesn't exist.
    """
    return db.query(Account).filter(Account.id == account_id).first()

def create_account(account_data: AccountCreate, db: Session):
    """
    Create a new Account. The user must supply:
      - user_id: an existing User
      - name: e.g. "Bank", "BTC Wallet", "BTC Fees"
      - currency: "USD" or "BTC"
    The DB enforces user_id not null, so user must exist or an FK error occurs.
    """
    new_account = Account(
        user_id=account_data.user_id,
        name=account_data.name,
        currency=account_data.currency,
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account

def update_account(account_id: int, account_data: AccountUpdate, db: Session):
    """
    Update an existing account's fields (name/currency). 
    If account doesn't exist, return None. 
    If you want to allow changing user_id, you can handle that as well.
    """
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
    """
    Delete the account by ID if it exists. 
    For double-entry, consider if the account has ledger history. 
    Often you'd archive instead of a hard delete to preserve records,
    but that's an application decision.
    """
    account = get_account_by_id(account_id, db)
    if not account:
        return False

    db.delete(account)
    db.commit()
    return True
