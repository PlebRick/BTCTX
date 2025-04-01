#!/usr/bin/env python
"""
backend/database.py

Sets up the SQLAlchemy database connection, session management, and helper functions for creating tables.
This file underpins the BitcoinTX double-entry system by ensuring all models (e.g., LedgerEntry, BitcoinLot, LotDisposal)
are registered with the ORM and created in the database.

Key Features:
- Loads environment variables from .env at project root
- Handles default SQLite or custom DB URLs
- Provides get_db() for FastAPI dependency injection
- Ensures six hardcoded accounts (IDs 1–6) are always present with an idempotent UPSERT approach
- Requires user registration via /register (no default user created)

Security & Compliance Notes:
- No default user is created; users must register via /register
- Use secure password hashing (handled in user model, e.g., bcrypt or passlib)
- For production, ensure HTTPS and secure session cookies if using session-based auth
- Logging is included for auditing critical operations
"""

import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import TypeDecorator, String
from sqlalchemy.exc import IntegrityError
import datetime

# ------------------------------------------------------------------
# 0) Logging Setup
# ------------------------------------------------------------------
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# 1) Environment Setup
# ------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

dotenv_path = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=dotenv_path)
logger.debug(f"Loaded .env from: {dotenv_path}")

# Database file setup
DATABASE_FILE_ENV = os.getenv("DATABASE_FILE", "backend/bitcoin_tracker.db")
DATABASE_FILE = (
    DATABASE_FILE_ENV if os.path.isabs(DATABASE_FILE_ENV)
    else os.path.join(PROJECT_ROOT, DATABASE_FILE_ENV)
)
db_dir = os.path.dirname(DATABASE_FILE)
if not os.path.exists(db_dir):
    os.makedirs(db_dir)
    print(f"Created directory for database: {db_dir}")
    logger.debug(f"Created directory: {db_dir}")
else:
    logger.debug(f"Database directory already exists: {db_dir}")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_FILE}")
print("DATABASE_URL used:", DATABASE_URL)
logger.debug(f"DATABASE_URL: {DATABASE_URL}")

# ------------------------------------------------------------------
# 2) SQLAlchemy Engine and Session Setup
# ------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite concurrency
)
logger.debug("SQLAlchemy engine created")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
logger.debug("SessionLocal factory created")

Base = declarative_base()
logger.debug("Base class defined for ORM models")

# ------------------------------------------------------------------
# 3) Custom UTC DateTime for SQLite
# ------------------------------------------------------------------
class UTCDateTime(TypeDecorator):
    """
    Stores Python datetime objects as ISO8601 strings with 'Z' in SQLite,
    ensuring they are read back as offset-aware UTC datetimes.
    """
    impl = String

    def process_bind_param(self, value, dialect):
        """Convert Python datetime -> string before saving to DB."""
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=datetime.timezone.utc)
        return value.isoformat().replace("+00:00", "Z")

    def process_result_value(self, value, dialect):
        """Convert string -> Python datetime (UTC) after fetching from DB."""
        if value is None:
            return None
        value = value.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(value)

# ------------------------------------------------------------------
# 4) FastAPI Dependency Injection
# ------------------------------------------------------------------
def get_db():
    """
    Provides a DB session for FastAPI routes. Yields a SessionLocal instance
    and closes it after use to prevent leaks.
    """
    db = SessionLocal()
    logger.debug("Created new database session for get_db")
    try:
        yield db
    finally:
        db.close()
        logger.debug("Closed database session in get_db")

# ------------------------------------------------------------------
# 5) Table Initialization & Fixed Account Seeding
# ------------------------------------------------------------------
def create_tables():
    """
    Initializes all database tables and ensures six hardcoded accounts with IDs 1–6 exist.
    Uses an idempotent UPSERT approach to insert or update accounts without breaking
    primary key constraints or auto-increment in SQLite.

    Fixed Accounts:
    - 1: Bank (USD)
    - 2: Wallet (BTC)
    - 3: Exchange USD (USD)
    - 4: Exchange BTC (BTC)
    - 5: BTC Fees (BTC)
    - 6: USD Fees (USD)

    Requires at least one user to exist (via /register). If no user exists, skips account creation.
    """
    print("Creating database tables...")
    logger.debug("Starting create_tables()")

    # Import models to register with Base.metadata
    try:
        from backend.models import account, transaction, user
        logger.debug("Imported models: account, transaction, user")
    except ImportError as e:
        print("Error importing models:", e)
        logger.error(f"ImportError during model import: {e}")
        raise e

    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.debug("Executed Base.metadata.create_all to create tables")

    db = SessionLocal()
    try:
        # Check for at least one user
        existing_user = db.query(user.User).first()
        if not existing_user:
            logger.warning("No user found. Skipping account creation.")
            print("Database tables created successfully (no user yet).")
            return

        user_id = existing_user.id
        logger.debug(f"Using user_id={user_id} for accounts")

        # Define the six fixed accounts
        fixed_accounts = [
            {"id": 1, "name": "Bank", "currency": "USD"},
            {"id": 2, "name": "Wallet", "currency": "BTC"},
            {"id": 3, "name": "Exchange USD", "currency": "USD"},
            {"id": 4, "name": "Exchange BTC", "currency": "BTC"},
            {"id": 5, "name": "BTC Fees", "currency": "BTC"},
            {"id": 6, "name": "USD Fees", "currency": "USD"},
        ]

        # Step 1: Log existing accounts before insert
        existing_accounts = db.query(account.Account).all()
        if existing_accounts:
            logger.debug(f"Accounts before initialization: {[(a.id, a.name, a.currency) for a in existing_accounts]}")
        else:
            logger.debug("No existing accounts found before initialization.")

        # Step 2: Try inserting or updating each fixed account
        for acct in fixed_accounts:
            try:
                existing = db.query(account.Account).filter_by(id=acct["id"]).first()
                if existing:
                    existing.name = acct["name"]
                    existing.currency = acct["currency"]
                    existing.user_id = user_id
                    logger.debug(f"Updated account ID={acct['id']} to name='{acct['name']}'")
                else:
                    new_acct = account.Account(
                        id=acct["id"],
                        user_id=user_id,
                        name=acct["name"],
                        currency=acct["currency"]
                    )
                    db.add(new_acct)
                    db.flush()  # 💥 force the insert to happen immediately
                    logger.debug(f"Inserted account ID={acct['id']} ({acct['name']})")
            except IntegrityError as e:
                logger.error(f"Insert failed for account ID={acct['id']} — likely ID conflict: {e}")
                db.rollback()
                raise
            except Exception as e:
                logger.error(f"Unexpected error on account ID={acct['id']}: {e}")
                db.rollback()
                raise

        # Step 3: Commit once after all inserts/updates
        db.commit()
        logger.info("Committed all account inserts/updates successfully.")

        # Step 4: Log final accounts for verification
        final_accounts = db.query(account.Account).order_by(account.Account.id).all()
        logger.info("Final state of accounts in the database:")
        for acct in final_accounts:
            logger.info(f"  ID={acct.id} | Name={acct.name} | Currency={acct.currency}")

        existing = db.query(account.Account.id).filter(account.Account.id.in_([1, 2, 3, 4, 5, 6])).all()
        found_ids = {row.id for row in existing}
        expected_ids = {1, 2, 3, 4, 5, 6}
        missing = expected_ids - found_ids
        if missing:
            raise RuntimeError(f"Missing core accounts: {missing}")

    except Exception as e:
        logger.error(f"Error during account setup: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        logger.debug("Closed database session in create_tables")

    print("Database tables created successfully.")
    logger.debug("Finished create_tables()")

# Optional: Run create_tables() on module import (e.g., for development)
if __name__ == "__main__":
    create_tables()