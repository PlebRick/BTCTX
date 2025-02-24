#!/usr/bin/env python
"""
deleteTransactions.py

A standalone script to delete all Transaction records from the BitcoinTX database.
This script will remove all transactions (and their cascaded records such as LedgerEntries,
BitcoinLots, and LotDisposals) while keeping user accounts and other non-transactional data intact.

Usage:
    python deleteTransactions.py
"""

import sys
import os

# Ensure the proper project path is set if needed; adjust PYTHONPATH as necessary.
# os.environ["PYTHONPATH"] = os.path.join(os.path.dirname(__file__), "..")

# Import the database session factory and the delete_all_transactions service function
from backend.database import SessionLocal
from backend.services import transaction as tx_service

def main():
    """
    Main entry point for the script.
    Creates a database session, deletes all transactions,
    and prints the count of deleted records.
    """
    # Create a new database session
    db = SessionLocal()
    try:
        # Call the service function that deletes all transactions.
        deleted_count = tx_service.delete_all_transactions(db)
        print(f"Successfully deleted {deleted_count} transactions.")
    except Exception as e:
        print("An error occurred while deleting transactions:", e)
        sys.exit(1)
    finally:
        # Always close the session to release database resources.
        db.close()

if __name__ == "__main__":
    main()