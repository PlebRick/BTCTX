"""
services/account.py

Refactored to be consistent with double-entry approach. 
No direct references to single-entry transaction logic exist here, 
so minimal changes are required. We simply reinforce:
  - Some account types (ExchangeUSD/ExchangeBTC) might only track 
    one currency in practice.
  - The create/update logic remains the same for user_id, type, and balances.
"""

from sqlalchemy.orm import Session
from backend.models.account import Account
from backend.schemas.account import AccountCreate, AccountUpdate

def get_all_accounts(db: Session):
    """
    Return all Account records in the database.
    """
    return db.query(Account).all()

def get_account_by_id(account_id: int, db: Session):
    """
    Return a single Account by its primary key.
    """
    return db.query(Account).filter(Account.id == account_id).first()

def create_account(account: AccountCreate, db: Session):
    """
    Create a new Account record.

    With the new double-entry design, we can have:
     - Bank
     - Wallet
     - ExchangeUSD
     - ExchangeBTC
    The user may specify initial balances (balance_usd, balance_btc).
    Typically, an 'ExchangeUSD' account might track only balance_usd
    (balance_btc = 0), and 'ExchangeBTC' might track only balance_btc
    (balance_usd = 0). But this isn't enforced at the DB level.
    """
    new_account = Account(
        user_id=account.user_id,
        type=account.type,
        balance_usd=account.balance_usd,
        balance_btc=account.balance_btc
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account

def update_account(account_id: int, account: AccountUpdate, db: Session):
    """
    Update an existing Account record. 
    In double-entry, changing account type from e.g. ExchangeUSD to Wallet
    might be unusual in production, but it's allowed here for flexibility.
    """
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if not db_account:
        return None

    # If fields are None in 'account', we skip them (or set them). 
    # For now, we assume we always set them directly.
    if account.type is not None:
        db_account.type = account.type
    if account.balance_usd is not None:
        db_account.balance_usd = account.balance_usd
    if account.balance_btc is not None:
        db_account.balance_btc = account.balance_btc

    db.commit()
    db.refresh(db_account)
    return db_account

def delete_account(account_id: int, db: Session):
    """
    Delete an existing Account record by its primary key.
    If found, remove it from DB. 
    Note: if transactions reference this account, 
    you may want to block or handle it carefully in a real system.
    """
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if db_account:
        db.delete(db_account)
        db.commit()
        return True
    return False
