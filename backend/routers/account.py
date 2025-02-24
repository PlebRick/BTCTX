"""
backend/routers/account.py

FastAPI router handling Account endpoints. In a double-entry system,
each Account may appear in many LedgerEntry lines, but the user typically
manages Accounts (create/update/delete) separately from transactions.

No major changes are required specifically for double-entry logic here,
since the ledger references are handled in transaction or ledger services.
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
    Retrieve all Accounts in the system. For a single-user scenario,
    you might filter by that user's ID, but here we show them all.
    """
    return account_service.get_all_accounts(db)

@router.get("/{account_id}", response_model=AccountRead)
def get_account(account_id: int, db = Depends(get_db)):
    """
    Retrieve a specific Account by its ID, or return 404 if not found.
    """
    account = account_service.get_account_by_id(account_id, db)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    return account

@router.post("/", response_model=AccountRead)
def create_account(account: AccountCreate, db = Depends(get_db)):
    """
    Create a new Account. The request body (AccountCreate) includes:
      - user_id: the owner
      - name: e.g. "Bank", "BTC Fees", "Wallet"
      - currency: "USD" or "BTC"

    The service layer handles the actual DB insertion.
    """
    new_account = account_service.create_account(account, db)
    return new_account

@router.put("/{account_id}", response_model=AccountRead)
def update_account(account_id: int, account: AccountUpdate, db = Depends(get_db)):
    """
    Update an existing Account's 'name' or 'currency' (both optional).
    Returns 404 if no such account exists.
    """
    updated_account = account_service.update_account(account_id, account, db)
    if not updated_account:
        raise HTTPException(status_code=404, detail="Account not found.")
    return updated_account

@router.delete("/{account_id}", status_code=204)
def delete_account(account_id: int, db = Depends(get_db)):
    """
    Delete an existing Account by ID, returning 204 on success.
    If the account doesn't exist or cannot be deleted (e.g. has references),
    return 404.
    """
    success = account_service.delete_account(account_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Account not found or cannot be deleted.")
    return