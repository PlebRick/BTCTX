"""
backend/routers/account.py

FastAPI router for Account endpoints.
Provides endpoints to list, retrieve, create, update, and delete accounts.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from backend.schemas.account import AccountCreate, AccountUpdate, AccountRead
from backend.services import account as account_service
from backend.database import get_db

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.get("/", response_model=List[AccountRead])
def list_accounts(db = Depends(get_db)):
    """Retrieve all accounts."""
    return account_service.get_all_accounts(db)

@router.get("/{account_id}", response_model=AccountRead)
def get_account(account_id: int, db = Depends(get_db)):
    """Retrieve a specific account by ID."""
    account = account_service.get_account_by_id(account_id, db)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    return account

@router.post("/", response_model=AccountRead)
def create_account(account: AccountCreate, db = Depends(get_db)):
    """Create a new account."""
    return account_service.create_account(account, db)

@router.put("/{account_id}", response_model=AccountRead)
def update_account(account_id: int, account: AccountUpdate, db = Depends(get_db)):
    """Update an existing account."""
    updated_account = account_service.update_account(account_id, account, db)
    if not updated_account:
        raise HTTPException(status_code=404, detail="Account not found.")
    return updated_account

@router.delete("/{account_id}", status_code=204)
def delete_account(account_id: int, db = Depends(get_db)):
    """Delete an account."""
    success = account_service.delete_account(account_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Account not found or cannot be deleted.")
    return
