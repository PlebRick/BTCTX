"""
backend/routers/transaction.py

Router for Transaction endpoints in a full double-entry environment.
The user might still pass single-entry fields (from_account_id, amount, etc.),
but the service transforms them into LedgerEntries plus optional BTC lot usage.

We keep these endpoints minimal, delegating actual multi-line ledger creation,
BTC lot tracking (BitcoinLot), and disposal (LotDisposal) to the service layer.

Refactor Notes:
 - Added 'test_*' endpoints as examples of how to create specific deposit/transfer
   transactions for testing or demonstration. These are marked "temporary" so you
   know they don't have to remain in production if you prefer to keep a single
   generic POST /api/transactions for everything.
 - Retained existing create/list/update/delete endpoints as your primary interface.
 - Provided extensive docstrings to clarify usage for new developers.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

# The Pydantic schemas for transaction CRUD
from backend.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionRead
)

# The service layer that handles double-entry creation, BTC lots, FIFO disposal, etc.
from backend.services import transaction as tx_service

# The FastAPI "dependency" for getting a database session
from backend.database import get_db

# Create a router instance
router = APIRouter(tags=["transactions"])

@router.get("/", response_model=List[TransactionRead])
def list_transactions(db: Session = Depends(get_db)):
    """
    List all transactions, typically in descending order by timestamp.
    
    - Returns a list of TransactionRead schemas, each representing a "header"
      with potential behind-the-scenes LedgerEntries, BTC lot usage, etc.
    - This is a standard "production" endpoint.
    """
    return tx_service.get_all_transactions(db)


@router.post("/", response_model=TransactionRead)
def create_transaction(tx: TransactionCreate, db: Session = Depends(get_db)):
    """
    Create a new transaction in the double-entry system.

    - The front end may supply 'from_account_id', 'to_account_id', 'amount',
      'fee_amount', etc.
    - The service layer:
        1) Builds LedgerEntries (MAIN_OUT, MAIN_IN, FEE) for each debit/credit.
        2) If it's a Deposit/Buy, creates a BitcoinLot.
        3) If it's a Withdrawal/Sell, disposes from existing lots (LotDisposal),
           computing partial or final cost basis if desired.
        4) Runs the double-entry balance check (if both sides are internal).
    - Returns the newly created Transaction with an 'id'.

    This endpoint is considered "production" and is the primary way to create
    any new transaction type. It's flexible enough to handle deposits, withdrawals,
    transfers, buys, sells, etc., depending on the data provided.
    """
    tx_data = tx.dict()
    new_tx = tx_service.create_transaction_record(tx_data, db)
    if not new_tx:
        raise HTTPException(status_code=400, detail="Transaction creation failed.")
    return new_tx


@router.put("/{transaction_id}", response_model=TransactionRead)
def update_transaction(transaction_id: int, tx: TransactionUpdate, db: Session = Depends(get_db)):
    """
    Update an existing transaction's data if it's not locked.
    
    - The service might remove old ledger lines/lot usage and re-create them
      if the user changed critical fields like amount or type.
    - If the transaction is locked or nonexistent, return 404 or 400.
    """
    tx_data = tx.dict(exclude_unset=True)
    updated_tx = tx_service.update_transaction_record(transaction_id, tx_data, db)
    if not updated_tx:
        raise HTTPException(status_code=404, detail="Transaction not found or is locked.")
    return updated_tx

@router.delete("/delete_all", status_code=204)
def delete_all_transactions_endpoint(db: Session = Depends(get_db)):
    """
    Delete all transactions from the database. This will remove all Transaction records,
    and cascade delete associated LedgerEntries, BitcoinLots, and LotDisposals.
    """
    deleted_count = tx_service.delete_all_transactions(db)
    return {"deleted_count": deleted_count}


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """
    Delete a transaction if it's not locked. The service layer also
    cascades removal of any LedgerEntries, BitcoinLots, or LotDisposals
    tied to this transaction.
    """
    success = tx_service.delete_transaction_record(transaction_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found or cannot be deleted.")
    return
