#!/usr/bin/env python
"""
database.py

Refactored for clarity about our new double-entry system:
 - No changes are required to handle from/to accounts, since this file
   only sets up the engine, session, and metadata.
 - The create_tables() function still imports account, transaction, user,
   but the transaction model itself now uses from_account_id and to_account_id.

All environment loading, path resolution, and DB creation remains the same.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# -----------------------
#   Environment Setup
# -----------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
dotenv_path = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=dotenv_path)

DATABASE_FILE_ENV = os.getenv("DATABASE_FILE", "backend/bitcoin_tracker.db")

# Convert relative DB path to absolute
if os.path.isabs(DATABASE_FILE_ENV):
    DATABASE_FILE = DATABASE_FILE_ENV
else:
    DATABASE_FILE = os.path.join(PROJECT_ROOT, DATABASE_FILE_ENV)

db_dir = os.path.dirname(DATABASE_FILE)
if not os.path.exists(db_dir):
    os.makedirs(db_dir)
    print(f"Created directory for database: {db_dir}")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_FILE}")

print("DATABASE_URL used:", DATABASE_URL)

# -----------------------
#   SQLAlchemy Engine
# -----------------------
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create a session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for ORM models
Base = declarative_base()

def create_tables():
    """
    Create all database tables defined by the ORM models.
    This includes our double-entry Transaction model (with from_account_id/to_account_id),
    along with Account, User, etc.
    """
    print("Creating database tables...")
    try:
        from backend.models import account, transaction, user
    except ImportError as e:
        print("Error importing models:", e)
        raise e

    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

def get_db():
    """
    Provide a database session for FastAPI routes or other components as a dependency.
    Yields a session and closes it after use, preventing resource leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
