#!/usr/bin/env python3

"""
Seed Transactions Script

Usage:
  python backend/tests/seed_transactions.py
"""

import sys
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# --- 1) Ensure backend modules are importable
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --- 2) Imports from backend
from backend.database import SessionLocal
from backend.services.transaction import create_transaction_record
from backend.schemas.transaction import TransactionCreate

# --- 3) JSON data location
SEED_TRANSACTIONS_FILE = THIS_FILE.parent / "transaction_seed_data.json"

def load_transactions():
    with open(SEED_TRANSACTIONS_FILE, "r", encoding="utf-8") as f:
        tx_list = json.load(f)
    tx_list.sort(key=lambda tx: (tx["timestamp"], tx["id"]))  # FIFO order
    return tx_list

def normalize_decimal_fields(tx: dict) -> dict:
    decimal_fields = [
        "amount",
        "fee_amount",
        "cost_basis_usd",
        "proceeds_usd",
        "realized_gain_usd",
        "fmv_usd",
        "gross_proceeds_usd"
    ]
    for field in decimal_fields:
        raw = tx.get(field)
        tx[field] = Decimal(str(raw)) if raw is not None else None
    return tx

def seed_transactions():
    db = SessionLocal()
    transactions = load_transactions()
    created = 0
    failed = 0

    for tx in transactions:
        try:
            tx = normalize_decimal_fields(tx)
            tx_data = TransactionCreate(**tx)
            created_tx = create_transaction_record(tx_data.model_dump(), db)
            created += 1
        except Exception as e:
            print(f"[ERROR] Failed to insert transaction {tx.get('id','?')}: {e}")
            db.rollback()
            failed += 1

    db.commit()
    db.close()

    print(f"✅ Seeded {created} transactions.")
    if failed:
        print(f"⚠️ {failed} transactions failed to insert.")

if __name__ == "__main__":
    seed_transactions()
