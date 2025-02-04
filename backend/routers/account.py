from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.models.account import Account
from backend.schemas.account import AccountCreate, AccountRead
from backend.database import SessionLocal
from backend.services.account import get_all_accounts, create_account as create_account_service

# Initialize APIRouter
router = APIRouter()

# --- Dependency to get the database session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Routes for account management ---

# GET all accounts
@router.get("/", response_model=List[AccountRead])
def get_accounts(db: Session = Depends(get_db)):
    # Option 1: Use the service for business logic separation
    # return get_all_accounts()

    # Option 2: Direct database query
    accounts = db.query(Account).all()
    return accounts

# POST: Create a new account
@router.post("/", response_model=AccountRead)
def create_new_account(account: AccountCreate, db: Session = Depends(get_db)):
    # Option 1: Use service method to handle business logic
    # return create_account_service(account)

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