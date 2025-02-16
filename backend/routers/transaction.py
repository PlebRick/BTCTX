"""
routers/transaction.py

Refactored for the double-entry Plan B approach:
  - Instead of a single account_id, the create/update schemas now provide from_account_id and to_account_id.
  - This router calls service functions (create_transaction_record, etc.) that expect the new schema fields.
  - Minimal changes here beyond docstrings, since the old code didn't explicitly reference 'transaction.account_id'.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.models.transaction import Transaction
from backend.schemas.transaction import (
    TransactionCreate,
    TransactionRead,
    TransactionUpdate
)
from backend.services.transaction import (
    get_all_transactions,
    get_transaction_by_id,
    create_transaction_record,
    update_transaction_record,
    delete_transaction_record
)

router = APIRouter()

@router.get("/", response_model=List[TransactionRead])
def get_transactions(db: Session = Depends(get_db)):
    """
    Retrieve all transactions, ordered by timestamp (descending).
    - Timestamps are treated as UTC for any historical price lookups/date-based logic.
    - Now returns TransactionRead, which includes from_account_id and to_account_id
      instead of a single account_id.
    """
    transactions = db.query(Transaction).order_by(Transaction.timestamp.desc()).all()
    return transactions

@router.post("", response_model=TransactionRead)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new transaction under the double-entry model.
    - The user now provides from_account_id and to_account_id in the request payload
      (instead of one account_id).
    - For example, a Deposit might have from_account_id=External, to_account_id=Wallet,
      a Withdrawal might invert that, etc.
    - Fee is always in USD (fee=some_value).
    - cost_basis_usd is stored if relevant (e.g., external BTC deposit).
    - The service layer checks if from/to accounts are valid and updates balances accordingly.
    """
    db_transaction = create_transaction_record(transaction, db)
    if not db_transaction:
        raise HTTPException(status_code=400, detail="Transaction could not be created.")
    return db_transaction

@router.put("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: int,
    transaction: TransactionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing transaction with partial fields (TransactionUpdate).
    - from_account_id, to_account_id, amounts, etc. can be changed if not locked.
    - If the transaction is locked (is_locked=True) and your business logic forbids changes,
      the service layer might reject the update.
    """
    db_transaction = update_transaction_record(transaction_id, transaction, db)
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found or locked.")
    return db_transaction

@router.delete("/{transaction_id}/", status_code=204)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a transaction by its ID.
    - The service layer may block deletion if the transaction is locked (is_locked=True).
    """
    success = delete_transaction_record(transaction_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return {"detail": "Transaction deleted successfully"}
