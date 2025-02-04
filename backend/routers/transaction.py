# /routers/transaction.py
# This file defines the API routes for transaction management in BitcoinTX.

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db  # Dependency for database sessions
from backend.models.transaction import Transaction
from backend.schemas.transaction import TransactionCreate, TransactionRead, TransactionUpdate

# Initialize APIRouter
router = APIRouter()

# --- Routes for transaction management ---

# GET: Retrieve all transactions
@router.get("/", response_model=List[TransactionRead])
def get_transactions(db: Session = Depends(get_db)):
    """
    Fetch all transactions from the database.

    Args:
        db (Session): Database session dependency.

    Returns:
        List[TransactionRead]: List of all transactions.
    """
    transactions = db.query(Transaction).all()
    return transactions

# POST: Create a new transaction
@router.post("/", response_model=TransactionRead)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    """
    Create a new transaction in the database.

    Args:
        transaction (TransactionCreate): Data for creating the transaction.
        db (Session): Database session dependency.

    Returns:
        TransactionRead: The newly created transaction.
    """
    db_transaction = Transaction(
        account_id=transaction.account_id,
        type=transaction.type,
        amount_usd=transaction.amount_usd,
        amount_btc=transaction.amount_btc,
        timestamp=transaction.timestamp,
        source=transaction.source,
        purpose=transaction.purpose,
        fee_currency=transaction.fee.currency if transaction.fee else None,
        fee_amount=transaction.fee.amount if transaction.fee else None
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

# PUT: Update an existing transaction
@router.put("/{transaction_id}", response_model=TransactionRead)
def update_transaction(transaction_id: int, transaction: TransactionUpdate, db: Session = Depends(get_db)):
    """
    Update an existing transaction in the database.

    Args:
        transaction_id (int): ID of the transaction to update.
        transaction (TransactionUpdate): Updated transaction data.
        db (Session): Database session dependency.

    Returns:
        TransactionRead: The updated transaction.
    """
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Update fields if they are provided
    if transaction.type:
        db_transaction.type = transaction.type
    if transaction.amount_usd is not None:
        db_transaction.amount_usd = transaction.amount_usd
    if transaction.amount_btc is not None:
        db_transaction.amount_btc = transaction.amount_btc
    if transaction.purpose:
        db_transaction.purpose = transaction.purpose
    if transaction.source:
        db_transaction.source = transaction.source
    if transaction.fee:
        db_transaction.fee_currency = transaction.fee.currency
        db_transaction.fee_amount = transaction.fee.amount

    db.commit()
    db.refresh(db_transaction)
    return db_transaction

# DELETE: Delete a transaction
@router.delete("/{transaction_id}/", status_code=204)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """
    Delete a transaction from the database.

    Args:
        transaction_id (int): ID of the transaction to delete.
        db (Session): Database session dependency.

    Returns:
        dict: Success message if the transaction was deleted.
    """
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(db_transaction)
    db.commit()
    return {"detail": "Transaction deleted successfully"}