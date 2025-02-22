"""
backend/routers/transaction.py

Router for Transaction endpoints in a full double-entry environment.
The user might still pass single-entry fields (from_account_id, amount, etc.),
but the service transforms them into LedgerEntries plus optional BTC lot usage.

We keep these endpoints minimal, delegating actual multi-line ledger creation,
BTC lot tracking (BitcoinLot), and disposal (LotDisposal) to the service layer.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from backend.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionRead
)
from backend.services import transaction as tx_service
from backend.database import get_db

router = APIRouter(tags=["transactions"])

@router.get("/", response_model=List[TransactionRead])
def list_transactions(db = Depends(get_db)):
    """
    List all transactions in descending order of timestamp.
    The service returns Transaction objects, each possibly
    having multiple LedgerEntries behind the scenes.
    """
    return tx_service.get_all_transactions(db)

@router.post("/", response_model=TransactionRead)
def create_transaction(tx: TransactionCreate, db = Depends(get_db)):
    """
    Create a new transaction in the double-entry system.

    The front end may supply 'from_account_id', 'to_account_id', 'amount',
    'fee_amount', etc. The service layer:
      - builds LedgerEntries for each debit/credit
      - if it's a Deposit/Buy, creates a BitcoinLot
      - if it's a Withdrawal/Sell, disposes from existing lots (LotDisposal)
      - calculates partial or final cost basis if desired

    Returns the newly created Transaction with an 'id'.
    """
    tx_data = tx.dict()
    new_tx = tx_service.create_transaction_record(tx_data, db)
    if not new_tx:
        raise HTTPException(status_code=400, detail="Transaction creation failed.")
    return new_tx

@router.put("/{transaction_id}", response_model=TransactionRead)
def update_transaction(transaction_id: int, tx: TransactionUpdate, db = Depends(get_db)):
    """
    Update an existing transaction's data if it's not locked.
    The service might remove old ledger lines/lot usage and re-create them
    if the user changed critical fields like amount or type.

    If the transaction is locked or nonexistent, return 404 or 400.
    """
    tx_data = tx.dict(exclude_unset=True)
    updated_tx = tx_service.update_transaction_record(transaction_id, tx_data, db)
    if not updated_tx:
        raise HTTPException(status_code=404, detail="Transaction not found or is locked.")
    return updated_tx

@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: int, db = Depends(get_db)):
    """
    Delete a transaction if it's not locked. The service layer also
    cascades removal of any LedgerEntries, BitcoinLots, or LotDisposals
    tied to this transaction. 
    """
    success = tx_service.delete_transaction_record(transaction_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found or cannot be deleted.")
    return
