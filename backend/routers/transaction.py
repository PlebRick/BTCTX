from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.models.transaction import Transaction
from backend.schemas.transaction import TransactionCreate, TransactionRead, TransactionUpdate
from backend.database import SessionLocal
from backend.services.transaction import get_all_transactions, create_transaction, update_transaction, delete_transaction

# Initialize APIRouter
router = APIRouter()

# --- Dependency to get the database session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Routes for transaction management ---

# GET all transactions with a fallback to the service or direct query
@router.get("/", response_model=List[TransactionRead])
def get_transactions(db: Session = Depends(get_db)):
    # Option 1: Use service to decouple business logic
    # return get_all_transactions()

    # Option 2: Use direct query (maintain flexibility for refactor)
    transactions = db.query(Transaction).all()
    return transactions

# POST: Create a new transaction
@router.post("/", response_model=TransactionRead)
def create_new_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    # Option 1: Use service method
    # return create_transaction(transaction)

    # Option 2: Direct creation inside route
    db_transaction = Transaction(
        account_id=transaction.account_id,
        type=transaction.type,
        amount_usd=transaction.amount_usd,
        amount_btc=transaction.amount_btc,
        purpose=transaction.purpose,
        source=transaction.source,
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

# PUT: Update an existing transaction
@router.put("/{transaction_id}", response_model=TransactionRead)
def update_existing_transaction(transaction_id: int, transaction: TransactionUpdate, db: Session = Depends(get_db)):
    # Option 1: Use service method
    # updated_transaction = update_transaction(transaction_id, transaction)
    # if not updated_transaction:
    #     raise HTTPException(status_code=404, detail="Transaction not found")
    # return updated_transaction

    # Option 2: Direct update inside route
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Update fields
    db_transaction.type = transaction.type
    db_transaction.amount_usd = transaction.amount_usd
    db_transaction.amount_btc = transaction.amount_btc
    db_transaction.purpose = transaction.purpose
    db_transaction.source = transaction.source

    db.commit()
    db.refresh(db_transaction)
    return db_transaction

# DELETE: Delete a transaction
@router.delete("/{transaction_id}/", status_code=204)
def delete_existing_transaction(transaction_id: int, db: Session = Depends(get_db)):
    # Option 1: Use service method
    # if not delete_transaction(transaction_id):
    #     raise HTTPException(status_code=404, detail="Transaction not found")

    # Option 2: Direct delete inside route
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(db_transaction)
    db.commit()
    return {"detail": "Transaction deleted successfully"}