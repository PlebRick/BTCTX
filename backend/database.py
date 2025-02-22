#!/usr/bin/env python
"""
backend/database.py

Sets up the SQLAlchemy database connection, session management,
and helper functions for creating tables. This file underpins
the new double-entry system by ensuring all models, including
LedgerEntry, BitcoinLot, and LotDisposal, are registered with
the ORM and created in the database.

Additionally:
 - Loads environment variables from .env at project root
 - Handles default SQLite or custom DB URLs
 - Provides get_db() for FastAPI dependency injection
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# ---------------------------------------------------------
# 1) Environment Setup
# ---------------------------------------------------------
# We detect the project root, load .env, then figure out
# the DB file path or a full DATABASE_URL if provided.

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

dotenv_path = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=dotenv_path)

# If no environment variable is set, we use "backend/bitcoin_tracker.db" by default
DATABASE_FILE_ENV = os.getenv("DATABASE_FILE", "backend/bitcoin_tracker.db")

# Convert relative DB path to absolute path if needed
if os.path.isabs(DATABASE_FILE_ENV):
    DATABASE_FILE = DATABASE_FILE_ENV
else:
    DATABASE_FILE = os.path.join(PROJECT_ROOT, DATABASE_FILE_ENV)

# Ensure the directory for the SQLite database exists.
db_dir = os.path.dirname(DATABASE_FILE)
if not os.path.exists(db_dir):
    os.makedirs(db_dir)
    print(f"Created directory for database: {db_dir}")

# A custom DATABASE_URL can override the default SQLite file
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_FILE}")
print("DATABASE_URL used:", DATABASE_URL)

# ---------------------------------------------------------
# 2) SQLAlchemy Engine and Session Setup
# ---------------------------------------------------------
# We create an engine for the chosen DB (e.g. SQLite),
# then set up a session factory for managing transactions.

from sqlalchemy.engine import Engine

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} 
    # For SQLite concurrency. Not needed for other DBs.
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# A 'Base' class for our ORM models to inherit.
Base = declarative_base()

# ---------------------------------------------------------
# 3) Dependency Injection for FastAPI
# ---------------------------------------------------------
def get_db():
    """
    Provides a DB session for FastAPI routes or other components.
    Yields a SessionLocal instance and closes it after use to prevent leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------
# 4) Helper Function: create_tables()
# ---------------------------------------------------------
def create_tables():
    """
    Creates all tables defined by our ORM models in the DB.

    - We must import 'account', 'transaction', 'user', etc. so
      that the ledger models (LedgerEntry, BitcoinLot, LotDisposal)
      and the Transaction, Account, User models are registered
      with Base.metadata.
    - Then Base.metadata.create_all(bind=engine) builds them
      according to the final double-entry schema.
    """
    print("Creating database tables...")
    try:
        # Importing models ensures classes (like LedgerEntry, BitcoinLot, etc.)
        # are registered with Base, so create_all() can see them.
        from backend.models import account, transaction, user

    except ImportError as e:
        print("Error importing models:", e)
        raise e

    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")
