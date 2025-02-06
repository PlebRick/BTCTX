# BitcoinTX_FastPYthon/backend/routers/transaction.py
"""
This module defines the API routes for transaction management in BitcoinTX.
It handles retrieving, creating, updating, and deleting transactions.
Transactions follow various types (Deposit, Withdrawal, Transfer, Buy, Sell)
and are validated via corresponding Pydantic schemas.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db  # Provides database session dependency
from backend.models.transaction import Transaction
from backend.schemas.transaction import TransactionCreate, TransactionRead, TransactionUpdate

router = APIRouter()

@router.get("/", response_model=List[TransactionRead])
def get_transactions(db: Session = Depends(get_db)):
    """
    Retrieve all transactions from the database, ordered by timestamp (newest first).
    
    Args:
        db (Session): Database session dependency.
    
    Returns:
        List[TransactionRead]: A list of transaction records.
    """
    transactions = db.query(Transaction).order_by(Transaction.timestamp.desc()).all()
    return transactions


@router.post("/", response_model=TransactionRead)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    """
    Create a new transaction in the database.
    
    The incoming payload follows the dynamic form rules and corresponds to one of
    the following transaction types: Deposit, Withdrawal, Transfer, Buy, or Sell.
    
    Args:
        transaction (TransactionCreate): Payload for creating the transaction.
        db (Session): Database session dependency.
    
    Returns:
        TransactionRead: The newly created transaction record.
    """
    # Create a new Transaction instance using the data from the TransactionCreate schema.
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


@router.put("/{transaction_id}", response_model=TransactionRead)
def update_transaction(transaction_id: int, transaction: TransactionUpdate, db: Session = Depends(get_db)):
    """
    Update an existing transaction.
    
    Only provided fields in the TransactionUpdate payload will be updated.
    
    Args:
        transaction_id (int): The ID of the transaction to update.
        transaction (TransactionUpdate): Payload with updated fields.
        db (Session): Database session dependency.
    
    Returns:
        TransactionRead: The updated transaction record.
    
    Raises:
        HTTPException: If the transaction with the specified ID does not exist.
    """
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Update only the fields that are provided in the update payload.
    if transaction.type is not None:
        db_transaction.type = transaction.type
    if transaction.amount_usd is not None:
        db_transaction.amount_usd = transaction.amount_usd
    if transaction.amount_btc is not None:
        db_transaction.amount_btc = transaction.amount_btc
    if transaction.purpose is not None:
        db_transaction.purpose = transaction.purpose
    if transaction.source is not None:
        db_transaction.source = transaction.source
    if transaction.fee:
        db_transaction.fee_currency = transaction.fee.currency
        db_transaction.fee_amount = transaction.fee.amount

    db.commit()
    db.refresh(db_transaction)
    return db_transaction


@router.delete("/{transaction_id}/", status_code=204)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """
    Delete a transaction from the database.
    
    Args:
        transaction_id (int): The ID of the transaction to delete.
        db (Session): Database session dependency.
    
    Returns:
        dict: A success message if the transaction was deleted.
    
    Raises:
        HTTPException: If the transaction is not found.
    """
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    db.delete(db_transaction)
    db.commit()
    return {"detail": "Transaction deleted successfully"}
