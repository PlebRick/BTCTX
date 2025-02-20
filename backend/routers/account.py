"""
backend/routers/account.py

FastAPI router for Account endpoints.
We can optionally ensure that only authorized users can create accounts,
but for now, we simply expect the user_id to be passed in the payload.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from backend.schemas.account import AccountCreate, AccountUpdate, AccountRead
from backend.services import account as account_service
from backend.database import get_db

router = APIRouter(tags=["accounts"])

@router.get("/", response_model=List[AccountRead])
def list_accounts(db = Depends(get_db)):
    """
    Retrieve all accounts in the system.
    For a single-user system, this might be all accounts for that user,
    or just a single account if you want an immediate filter.
    """
    return account_service.get_all_accounts(db)

@router.get("/{account_id}", response_model=AccountRead)
def get_account(account_id: int, db = Depends(get_db)):
    """
    Retrieve a specific account by ID.
    Raises 404 if the account doesn't exist.
    """
    account = account_service.get_account_by_id(account_id, db)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    return account

@router.post("/", response_model=AccountRead)
def create_account(account: AccountCreate, db = Depends(get_db)):
    """
    Create a new account.
    The request body must include:
      {
        "user_id": 1,    # The user that owns the account
        "name": "Bank",
        "currency": "USD"
      }
    """
    new_account = account_service.create_account(account, db)
    return new_account

@router.put("/{account_id}", response_model=AccountRead)
def update_account(account_id: int, account: AccountUpdate, db = Depends(get_db)):
    """
    Update an existing account by its ID.
    For example, change its 'name' or 'currency'.
    Raises 404 if not found.
    """
    updated_account = account_service.update_account(account_id, account, db)
    if not updated_account:
        raise HTTPException(status_code=404, detail="Account not found.")
    return updated_account

@router.delete("/{account_id}", status_code=204)
def delete_account(account_id: int, db = Depends(get_db)):
    """
    Delete an existing account by its ID.
    Raises 404 if not found.
    """
    success = account_service.delete_account(account_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Account not found or cannot be deleted.")
    return
