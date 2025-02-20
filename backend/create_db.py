#!/usr/bin/env python
"""
create_db.py

This script initializes the database tables for BitcoinTX by calling the
create_tables() function defined in backend/database.py.

Since we've switched to a single-amount, double-entry approach (and
reintroduced source/purpose fields), ensure your 'database.py' contains
the updated models so this script creates the correct tables.

Usage:
    python backend/create_db.py
"""

import sys
import os

# Determine the project root (one level above current file).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add the project root to sys.path if it's not already there.
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    print(f"Project root added to sys.path: {PROJECT_ROOT}")
else:
    print(f"Project root already in sys.path: {PROJECT_ROOT}")

# Import the create_tables function from database.py.
try:
    from backend.database import create_tables
except ImportError as e:
    print("Error importing create_tables from backend.database:", e)
    sys.exit(1)

if __name__ == "__main__":
    try:
        print("Creating database tables with updated models...")
        create_tables()
        print("Database tables created successfully.")
    except Exception as e:
        print("Error creating database tables:", e)
        sys.exit(1)
