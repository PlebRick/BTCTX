# backend/scripts/seed_transactions.py

import os
import sys
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Dynamically add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from backend.database import SessionLocal
from backend.services.transaction import create_transaction_record
from backend.models.transaction import Transaction
from backend.schemas.transaction import TransactionCreate

# 🧠 Seed data (in correct order)
SEED_TRANSACTIONS_FILE = "backend/scripts/transaction_seed_data.json"


def load_transactions():
    with open(SEED_TRANSACTIONS_FILE, "r") as f:
        tx_list = json.load(f)
    # Sort by timestamp then ID, matching scorched-earth ordering
    tx_list.sort(key=lambda tx: (tx["timestamp"], tx["id"]))
    return tx_list


def normalize_decimal_fields(tx: dict) -> dict:
    """Ensures Decimal precision for all expected fields."""
    decimal_fields = [
        "amount", "fee_amount", "cost_basis_usd",
        "proceeds_usd", "realized_gain_usd"
    ]
    for field in decimal_fields:
        if field in tx and tx[field] is not None:
            tx[field] = Decimal(tx[field])
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
            tx_data = TransactionCreate(**tx)
            create_transaction_record(tx_data.dict(), db)
            created += 1
        except Exception as e:
            print(f"[ERROR] Failed to insert transaction {tx['id']}: {e}")
            db.rollback()

    db.commit()
    db.close()
    print(f"✅ Seeded {created} transactions.")


if __name__ == "__main__":
    seed_transactions()
