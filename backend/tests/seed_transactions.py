#!/usr/bin/env python3
"""
Seed Transactions Script

Usage:
  python backend/tests/seed_transactions.py

This script:
  1) Loads transaction_seed_data.json
  2) Normalizes numeric fields to Decimal
  3) Inserts each transaction via create_transaction_record(...)
"""

import sys
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# --- 1) Ensure we can import from 'backend' if script is run directly. ---
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]  # e.g. /yourproject
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import SessionLocal
from backend.services.transaction import create_transaction_record
from backend.schemas.transaction import TransactionCreate

# Location of the seed JSON
SEED_TRANSACTIONS_FILE = (THIS_FILE.parent / "transaction_seed_data.json").resolve()

def load_transactions():
    with open(SEED_TRANSACTIONS_FILE, "r", encoding="utf-8") as f:
        tx_list = json.load(f)
    # Sort by timestamp then ID, so scorched-earth logic applies in correct order
    tx_list.sort(key=lambda tx: (tx["timestamp"], tx["id"]))
    return tx_list

def normalize_decimal_fields(tx: dict) -> dict:
    """
    Ensures Decimal precision for typical numeric fields.
    Updated to include 'gross_proceeds_usd' for the new schema.
    """
    decimal_fields = [
        "amount",
        "fee_amount",
        "cost_basis_usd",
        "proceeds_usd",
        "realized_gain_usd",
        "fmv_usd",
        "gross_proceeds_usd"  # <-- ADDED for the refactored system
    ]
    for field in decimal_fields:
        raw = tx.get(field)
        if raw is not None:
            tx[field] = Decimal(str(raw))
        else:
            tx[field] = None
    return tx

def seed_transactions():
    db = SessionLocal()
    transactions = load_transactions()
    created = 0

    for tx in transactions:
        try:
            tx = normalize_decimal_fields(tx)
            # Convert to Pydantic schema
            tx_data = TransactionCreate(**tx)
            create_transaction_record(tx_data.dict(), db)
            created += 1
        except Exception as e:
            print(f"[ERROR] Failed to insert transaction {tx.get('id','?')}: {e}")
            db.rollback()

    db.commit()
    db.close()
    print(f"✅ Seeded {created} transactions.")

if __name__ == "__main__":
    seed_transactions()
