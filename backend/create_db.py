#!/usr/bin/env python
"""
create_db.py

Initializes the SQLite database for BitcoinTX by calling 'create_tables()'
from 'backend/database.py'. This will ensure all tables—Transaction,
LedgerEntry, BitcoinLot, LotDisposal, etc.—are created in the DB.

We've refactored the system for a full double-entry approach, so this
script no longer references any old enums like TransactionType. It simply
imports 'create_tables()', which handles all model imports internally.

Usage:
    python backend/create_db.py
"""

import sys
import os

# 1) Determine the project root, which is one level above this file's directory.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2) Add the project root to sys.path so Python can locate 'backend' modules if needed.
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    print(f"Project root added to sys.path: {PROJECT_ROOT}")
else:
    print(f"Project root already in sys.path: {PROJECT_ROOT}")

# 3) Import 'create_tables' from 'database.py' (no references to TransactionType).
try:
    from backend.database import create_tables
except ImportError as e:
    print("Error importing create_tables from backend.database:", e)
    sys.exit(1)

# 4) Run create_tables() to build the tables. 
#    The double-entry models (Transaction, LedgerEntry, BitcoinLot, LotDisposal)
#    and any legacy references are automatically handled there.
if __name__ == "__main__":
    try:
        print("Creating database tables with updated double-entry models...")
        create_tables()
        print("Database tables created successfully.")
    except Exception as e:
        print("Error creating database tables:", e)
        sys.exit(1)
