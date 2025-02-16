"""
routers/account.py

Refactored to be consistent with the double-entry system, which
now supports separate ExchangeUSD and ExchangeBTC accounts if desired.

No direct changes were required to support from_account_id / to_account_id,
since this router deals only with Account creation/listing. We simply add
comments indicating best practices for double-entry usage.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.models.account import Account
from backend.schemas.account import AccountCreate, AccountRead
from backend.database import SessionLocal
from backend.services.account import (
    get_all_accounts,
    create_account as create_account_service
)

# Initialize APIRouter
router = APIRouter()

# -------------------------------------------------------------------
#   Dependency to get a DB Session
# -------------------------------------------------------------------
def get_db():
    """
    Provides a SQLAlchemy Session using SessionLocal, ensuring the session
    is closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------------------------------------------
#   Routes for Account Management
# -------------------------------------------------------------------

@router.get("/", response_model=List[AccountRead])
def get_accounts(db: Session = Depends(get_db)):
    """
    Retrieve all accounts in the database.
    
    Currently, this route performs a direct query:
      accounts = db.query(Account).all()
    Alternatively, you can call the service function get_all_accounts()
    for consistency in business logic.
    """
    # Option 1: Use the service function
    # return get_all_accounts(db)

    # Option 2: Direct query
    accounts = db.query(Account).all()
    return accounts

@router.post("/", response_model=AccountRead)
def create_new_account(account: AccountCreate, db: Session = Depends(get_db)):
    """
    Create a new account (e.g. Bank, Wallet, ExchangeUSD, ExchangeBTC, etc.).
    We keep it simple here:
      - Insert an Account row with the specified user_id, type, and balances.
      - In a real system, you might have additional checks or logic
        (e.g., ensuring user exists, limiting certain types).
    
    Example usage:
      POST /accounts
      {
        "user_id": 1,
        "type": "ExchangeUSD",
        "balance_usd": 1000.00,
        "balance_btc": 0.0
      }
    """
    # Option 1: Use a service function for logic
    # return create_account_service(account, db)

    # Option 2: Direct logic inside the route
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
