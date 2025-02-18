"""
backend/routers/transaction.py

FastAPI router for Transaction endpoints.
Handles endpoints for listing, creating, updating, and deleting transactions.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from backend.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionRead
from backend.services import transaction as tx_service
from backend.database import get_db

# --- Initialize Router ---
router = APIRouter(tags=["transactions"])

@router.get("/", response_model=List[TransactionRead])
def list_transactions(db = Depends(get_db)):
    """List all transactions."""
    return tx_service.get_all_transactions(db)

@router.post("/", response_model=TransactionRead)
def create_transaction(tx: TransactionCreate, db = Depends(get_db)):
    """
    Create a new transaction.
    
    The payload must include from_account_id, to_account_id, type, amount, and optionally fee, proceeds, etc.
    For BUY/SELL, both sides are expected and cost basis and realized gain will be computed.
    """
    # Convert Pydantic model to dict for our service function.
    tx_data = tx.dict()
    new_tx = tx_service.create_transaction_record(tx_data, db)
    if not new_tx:
        raise HTTPException(status_code=400, detail="Transaction creation failed.")
    return new_tx

@router.put("/{transaction_id}", response_model=TransactionRead)
def update_transaction(transaction_id: int, tx: TransactionUpdate, db = Depends(get_db)):
    """
    Update an existing transaction.
    Locked transactions cannot be updated.
    """
    tx_data = tx.dict(exclude_unset=True)
    updated_tx = tx_service.update_transaction_record(transaction_id, tx_data, db)
    if not updated_tx:
        raise HTTPException(status_code=404, detail="Transaction not found or is locked.")
    return updated_tx

@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: int, db = Depends(get_db)):
    """
    Delete a transaction if it is not locked.
    """
    success = tx_service.delete_transaction_record(transaction_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found or cannot be deleted.")
    return
