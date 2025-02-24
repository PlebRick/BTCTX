# backend/routers/reporting.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db

# Reporting service for balances and gains/losses
from backend.services.reporting import (
    get_all_account_balances,
    get_account_balance,
    get_gains_and_losses
)

# If you want to validate that an account exists, we import account service
from backend.services import account as account_service

router = APIRouter(
    tags=["reporting"]
)

@router.get("/balances")
def read_all_balances(db: Session = Depends(get_db)):
    """
    Return a list of all accounts with their computed ledger-based balance.

    The 'get_all_account_balances' function sums LedgerEntry.amounts for each Account.
    We convert Decimal balances to float for JSON serialization.
    """
    results = get_all_account_balances(db)
    for item in results:
        item["balance"] = float(item["balance"])
    return results

@router.get("/{account_id}/balance")
def read_account_balance(account_id: int, db: Session = Depends(get_db)):
    """
    Return a single account's computed ledger-based balance.

    Uses 'get_account_balance' to sum all LedgerEntries for the given account_id.
    If the account doesn't exist, raise 404.
    """
    # Validate the account actually exists if you want (optional)
    account = account_service.get_account_by_id(account_id, db)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")

    bal = get_account_balance(db, account_id)
    return {"account_id": account_id, "balance": float(bal)}

@router.get("/gains-losses")
def read_gains_losses(db: Session = Depends(get_db)):
    """
    Return realized gains, losses, and other gains from the transaction ledger.

    'get_gains_and_losses' aggregates short-term vs. long-term gains/losses,
    plus any custom logic for "other gains" (Income, Interest, etc.).
    """
    data = get_gains_and_losses(db)
    # If you want to convert any floats/decimals in `data`, do so here, else return as-is.
    return data
