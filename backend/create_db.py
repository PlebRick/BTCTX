#!/usr/bin/env python
"""
create_db.py

This script initializes the database tables for BitcoinTX by calling the
create_tables() function defined in backend/database.py.

It ensures that the project root is added to sys.path so that all modules
in the 'backend' package are found correctly. This is especially important
when running the script from the 'backend' directory.

Usage:
    From the project root or the backend folder, run:
        python backend/create_db.py
"""

import sys
import os

# Determine the project root.
# Our project structure is as follows:
# BitcoinTX_FastPython/
# ├── backend/
# │   ├── create_db.py
# │   └── database.py
# └── (other directories)
#
# Since create_db.py is inside the backend folder, the project root is one level above.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add the project root to sys.path if it's not already present.
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    print(f"Project root added to sys.path: {PROJECT_ROOT}")
else:
    print(f"Project root already in sys.path: {PROJECT_ROOT}")

# Now, try to import the create_tables function from backend/database.py.
try:
    from backend.database import create_tables
except ImportError as e:
    print("Error importing create_tables from backend.database:", e)
    sys.exit(1)

# Main execution block: call create_tables and handle any exceptions.
if __name__ == "__main__":
    try:
        print("Creating database tables...")
        create_tables()
        print("Database tables created successfully.")
    except Exception as e:
        print("Error creating database tables:", e)
        sys.exit(1)