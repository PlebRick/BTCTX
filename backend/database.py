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
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# ------------------------------------------------------------------
# NEW: We import the necessary pieces to define a custom TypeDecorator
# for offset-aware UTC datetimes in SQLite.
# ------------------------------------------------------------------
from sqlalchemy.types import TypeDecorator, String
import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# 1) Environment Setup
# ---------------------------------------------------------
# We detect the project root, load .env, then figure out
# the DB file path or a full DATABASE_URL if provided.

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
logger.debug(f"BASE_DIR: {BASE_DIR}, PROJECT_ROOT: {PROJECT_ROOT}")

dotenv_path = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=dotenv_path)
logger.debug(f"Loaded .env from: {dotenv_path}")

# If no environment variable is set, we use "backend/bitcoin_tracker.db" by default
DATABASE_FILE_ENV = os.getenv("DATABASE_FILE", "backend/bitcoin_tracker.db")
logger.debug(f"DATABASE_FILE_ENV from env: {DATABASE_FILE_ENV}")

# Convert relative DB path to absolute path if needed
if os.path.isabs(DATABASE_FILE_ENV):
    DATABASE_FILE = DATABASE_FILE_ENV
else:
    DATABASE_FILE = os.path.join(PROJECT_ROOT, DATABASE_FILE_ENV)
logger.debug(f"DATABASE_FILE resolved to: {DATABASE_FILE}")

# Ensure the directory for the SQLite database exists.
db_dir = os.path.dirname(DATABASE_FILE)
if not os.path.exists(db_dir):
    os.makedirs(db_dir)
    print(f"Created directory for database: {db_dir}")
    logger.debug(f"Created directory: {db_dir}")
else:
    logger.debug(f"Database directory already exists: {db_dir}")

# A custom DATABASE_URL can override the default SQLite file
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_FILE}")
print("DATABASE_URL used:", DATABASE_URL)
logger.debug(f"DATABASE_URL: {DATABASE_URL}")

# ---------------------------------------------------------
# 2) SQLAlchemy Engine and Session Setup
# ---------------------------------------------------------
# We create an engine for the chosen DB (e.g. SQLite),
# then set up a session factory for managing transactions.

from sqlalchemy.engine import Engine

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # For SQLite concurrency. Not needed for other DBs.
)
logger.debug("SQLAlchemy engine created")

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
logger.debug("SessionLocal factory created")

Base = declarative_base()
logger.debug("Base class defined for ORM models")

# ------------------------------------------------------------------
# NEW: A full custom TypeDecorator for offset-aware UTC in SQLite
# ------------------------------------------------------------------
class UTCDateTime(TypeDecorator):
    """
    Stores Python datetime objects as ISO8601 strings with 'Z' in SQLite,
    ensuring we read them back as offset-aware datetimes in UTC.
    """
    impl = String  # We'll store as TEXT under the hood.

    def process_bind_param(self, value, dialect):
        """Convert Python datetime -> string before saving to DB."""
        if value is None:
            return None
        if value.tzinfo is None:
            # If it's naive, assume it's in UTC
            value = value.replace(tzinfo=datetime.timezone.utc)
        # Convert to ISO8601 with a 'Z' suffix
        return value.isoformat().replace("+00:00", "Z")

    def process_result_value(self, value, dialect):
        """Convert string -> Python datetime (UTC) after fetching from DB."""
        if value is None:
            return None
        # Replace 'Z' with '+00:00' so datetime.fromisoformat can parse
        value = value.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(value)

# ---------------------------------------------------------
# 3) Dependency Injection for FastAPI
# ---------------------------------------------------------
def get_db():
    """
    Provides a DB session for FastAPI routes or other components.
    Yields a SessionLocal instance and closes it after use to prevent leaks.
    """
    db = SessionLocal()
    logger.debug("Created new database session for get_db")
    try:
        yield db
    finally:
        db.close()
        logger.debug("Closed database session in get_db")

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
    logger.debug("Starting create_tables")
    
    try:
        # Importing models ensures classes (like LedgerEntry, BitcoinLot, etc.)
        # are registered with Base, so create_all() can see them.
        from backend.models import account, transaction, user
        logger.debug("Imported models: account, transaction, user")
    except ImportError as e:
        print("Error importing models:", e)
        logger.error(f"ImportError during model import: {e}")
        raise e
    
    Base.metadata.create_all(bind=engine)
    logger.debug("Executed Base.metadata.create_all to create tables")
    
    db = SessionLocal()
    try:
        # Log existing accounts before any creation
        existing_accounts = db.query(account.Account).all()
        logger.debug(f"Accounts before initialization: {[(a.id, a.name, a.currency) for a in existing_accounts] if existing_accounts else 'None'}")
        
        # Ensure a default user exists
        if not db.query(user.User).filter_by(username="default").first():
            default_user = user.User(username="default")
            default_user.set_password("default_password")
            db.add(default_user)
            db.commit()
            logger.debug(f"Created default user with id={default_user.id}")
        else:
            logger.debug("Default user already exists")
        
        # Get user_id for account creation
        user_id = db.query(user.User).filter_by(username="default").first().id
        logger.debug(f"Using user_id={user_id} for accounts")
        
        # Define all required accounts
        all_accounts = [
            {"name": "Bank", "currency": "USD"},
            {"name": "Wallet", "currency": "BTC"},
            {"name": "Exchange USD", "currency": "USD"},
            {"name": "Exchange BTC", "currency": "BTC"},
            {"name": "BTC Fees", "currency": "BTC"},
            {"name": "USD Fees", "currency": "USD"}
        ]
        
        # Create accounts if they don’t exist
        for acct in all_accounts:
            if not db.query(account.Account).filter_by(name=acct["name"]).first():
                db.add(account.Account(user_id=user_id, name=acct["name"], currency=acct["currency"]))
                logger.debug(f"Created account: {acct['name']}")
        
        db.commit()
        logger.debug("Committed all accounts")
        
        # Log final state
        final_accounts = db.query(account.Account).all()
        logger.debug(f"Final accounts: {[(a.id, a.name, a.currency) for a in final_accounts]}")
    except Exception as e:
        logger.error(f"Error during account initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        logger.debug("Closed database session")
    
    print("Database tables created successfully.")
    logger.debug("Finished create_tables")
