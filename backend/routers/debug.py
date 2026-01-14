# File: backend/routers/debug.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.transaction import BitcoinLot, LotDisposal, LedgerEntry, Transaction

router = APIRouter()

@router.get("/lots", tags=["Debug"])
def list_all_lots(db: Session = Depends(get_db)):
    """
    Returns all BitcoinLot records with relevant fields.
    Good for debugging FIFO or cost basis totals.
    """
    lots = db.query(BitcoinLot).all()
    results = []
    for lot in lots:
        results.append({
            "id": lot.id,
            "created_txn_id": lot.created_txn_id,
            "acquired_date": lot.acquired_date,
            "total_btc": str(lot.total_btc),
            "remaining_btc": str(lot.remaining_btc),
            "cost_basis_usd": str(lot.cost_basis_usd),
            "lot_disposals": [disp.id for disp in lot.lot_disposals]  # e.g. list of disposal IDs
        })
    return results

@router.get("/lots/{lot_id}", tags=["Debug"])
def get_one_lot(lot_id: int, db: Session = Depends(get_db)):
    """
    Returns a single BitcoinLot with its disposal info.
    """
    lot = db.get(BitcoinLot, lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found.")
    
    # Build a detailed view
    lot_data = {
        "id": lot.id,
        "created_txn_id": lot.created_txn_id,
        "acquired_date": lot.acquired_date,
        "total_btc": str(lot.total_btc),
        "remaining_btc": str(lot.remaining_btc),
        "cost_basis_usd": str(lot.cost_basis_usd),
        "disposals": []
    }
    for disp in lot.lot_disposals:
        lot_data["disposals"].append({
            "id": disp.id,
            "disposed_btc": str(disp.disposed_btc),
            "transaction_id": disp.transaction_id,
            "disposal_basis_usd": str(disp.disposal_basis_usd),
            "proceeds_usd_for_that_portion": str(disp.proceeds_usd_for_that_portion),
            "realized_gain_usd": str(disp.realized_gain_usd),
            "holding_period": disp.holding_period
        })
    return lot_data

@router.get("/disposals", tags=["Debug"])
def list_all_disposals(db: Session = Depends(get_db)):
    """
    Returns all LotDisposal records. Helps debug partial-lot usage.
    """
    disposals = db.query(LotDisposal).all()
    results = []
    for d in disposals:
        results.append({
            "id": d.id,
            "lot_id": d.lot_id,
            "transaction_id": d.transaction_id,
            "disposed_btc": str(d.disposed_btc),
            "disposal_basis_usd": str(d.disposal_basis_usd),
            "proceeds_usd_for_that_portion": str(d.proceeds_usd_for_that_portion),
            "realized_gain_usd": str(d.realized_gain_usd),
            "holding_period": d.holding_period
        })
    return results

@router.get("/ledger-entries", tags=["Debug"])
def list_all_ledger_entries(db: Session = Depends(get_db)):
    """
    Returns all LedgerEntry records for double-entry debugging.
    """
    entries = db.query(LedgerEntry).all()
    results = []
    for e in entries:
        results.append({
            "id": e.id,
            "transaction_id": e.transaction_id,
            "account_id": e.account_id,
            "amount": str(e.amount),
            "currency": e.currency,
            "entry_type": e.entry_type
        })
    return results

@router.get("/transactions/{tx_id}/ledger-entries", tags=["Debug"])
def transaction_ledger_entries(tx_id: int, db: Session = Depends(get_db)):
    """
    Returns all ledger entries for a given transaction ID.
    """
    entries = db.query(LedgerEntry).filter(LedgerEntry.transaction_id == tx_id).all()
    if not entries:
        raise HTTPException(status_code=404, detail="No ledger entries found for that TX")
    results = []
    for e in entries:
        results.append({
            "id": e.id,
            "transaction_id": e.transaction_id,
            "account_id": e.account_id,
            "amount": str(e.amount),
            "currency": e.currency,
            "entry_type": e.entry_type
        })
    return results
