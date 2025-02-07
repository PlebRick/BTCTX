"""
routers/transaction.py

Refined to:
 - Accept and store costBasisUSD via the schemas.
 - Use a single 'fee' field in USD.
 - Mention that timestamps are treated as UTC.
 - Provide basic create/read/update/delete endpoints.
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
    Retrieve all transactions from the database, ordered by timestamp (desc).
    Timestamps are considered UTC for any historical price lookups or date-based logic.
    """
    transactions = db.query(Transaction).order_by(Transaction.timestamp.desc()).all()
    return transactions

@router.post("/", response_model=TransactionRead)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new transaction.
    If the type is 'Deposit' and the user enters cost_basis_usd, we store it.
    Fee is now always in USD, so no fee_currency required.
    Timestamps are stored as UTC by convention (though we do not forcibly convert naive datetimes here).
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
    Update an existing transaction.
    If is_locked is True, future logic might block changes (placeholder).
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
    Future logic might forbid deletion if is_locked is True.
    """
    success = delete_transaction_record(transaction_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return {"detail": "Transaction deleted successfully"}
