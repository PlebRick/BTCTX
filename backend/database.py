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
 - Gates "default user" creation behind a DEBUG-mode env var
   to avoid shipping insecure credentials to production.

IRS COMPLIANCE & SECURITY NOTES:
 - Do NOT hardcode or auto-create a default user in production.
 - Ensure password hashing is used (bcrypt or passlib).
 - For session-based auth, use HTTPS and secure cookies
   (SessionMiddleware with secure=True, https_only=True).
 - Consider logging or audit trails for critical DB operations.
"""

import os
import logging
import datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import TypeDecorator, String

# ------------------------------------------------------------------
# 0) Logging Setup
# ------------------------------------------------------------------
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# 1) Environment Setup
# ------------------------------------------------------------------

# Current file: <project_root>/backend/database.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
logger.debug(f"BASE_DIR: {BASE_DIR}, PROJECT_ROOT: {PROJECT_ROOT}")

# Load .env from project root
dotenv_path = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=dotenv_path)
logger.debug(f"Loaded .env from: {dotenv_path}")

# Get main DB file path or fallback to 'backend/bitcoin_tracker.db'
DATABASE_FILE_ENV = os.getenv("DATABASE_FILE", "backend/bitcoin_tracker.db")
logger.debug(f"DATABASE_FILE_ENV: {DATABASE_FILE_ENV}")

# Convert relative path to absolute if needed
if os.path.isabs(DATABASE_FILE_ENV):
    DATABASE_FILE = DATABASE_FILE_ENV
else:
    DATABASE_FILE = os.path.join(PROJECT_ROOT, DATABASE_FILE_ENV)
logger.debug(f"Resolved DATABASE_FILE: {DATABASE_FILE}")

# Ensure the directory for the SQLite database exists
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

# Check if we're in DEBUG mode (for dev/test only)
DEBUG_MODE = os.getenv("DEBUG", "False").lower() == "true"
logger.debug(f"DEBUG_MODE: {DEBUG_MODE}")

# ------------------------------------------------------------------
# 2) SQLAlchemy Engine and Session Setup
# ------------------------------------------------------------------

engine: Engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite concurrency
)
logger.debug("SQLAlchemy engine created")

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
logger.debug("SessionLocal factory created")

Base = declarative_base()
logger.debug("Declarative Base class defined")

# ------------------------------------------------------------------
# 3) Custom TypeDecorator for UTC DateTime in SQLite
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
            # If naive, assume UTC
            value = value.replace(tzinfo=datetime.timezone.utc)
        # Convert to ISO8601 with 'Z' suffix
        return value.isoformat().replace("+00:00", "Z")

    def process_result_value(self, value, dialect):
        """Convert string -> Python datetime (UTC) after fetching from DB."""
        if value is None:
            return None
        # Replace 'Z' with '+00:00' so datetime.fromisoformat can parse
        value = value.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(value)

# ------------------------------------------------------------------
# 4) Dependency Injection for FastAPI
# ------------------------------------------------------------------

def get_db():
    """
    Provides a DB session for FastAPI routes or other components.
    Yields a SessionLocal instance, then closes it to prevent leaks.
    """
    db = SessionLocal()
    logger.debug("Created new database session for get_db")
    try:
        yield db
    finally:
        db.close()
        logger.debug("Closed database session in get_db")

# ------------------------------------------------------------------
# 5) create_tables(): Create All DB Models & (Optionally) Seed Defaults
# ------------------------------------------------------------------

def create_tables():
    """
    Creates all tables defined by our ORM models in the database.

    - Dynamically imports account, transaction, user models so that
      the ledger system (LedgerEntry, BitcoinLot, etc.) and main
      tables (Transaction, Account, User) are registered with Base.
    - Then calls Base.metadata.create_all(bind=engine).

    By default, DOES NOT create any default user in production.
    If DEBUG_MODE == True, a 'default' user is auto-created for dev/test.

    Accounts will only be seeded if a user exists (either dev user
    or one manually created via /register).

    IRS COMPLIANCE (Production):
    - Do NOT ship insecure credentials or auto-create users with
      known passwords.
    - Ensure real users are created via the secure /register flow.
    """
    print("Creating database tables...")
    logger.debug("Starting create_tables")

    try:
        from backend.models import account, transaction, user
        logger.debug("Imported models: account, transaction, user")
    except ImportError as e:
        print("Error importing models:", e)
        logger.error(f"ImportError during model import: {e}")
        raise e

    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.debug("Executed Base.metadata.create_all for all models")

    db = SessionLocal()
    try:
        # If in DEBUG mode, create a default user for local dev only
        if DEBUG_MODE:
            logger.debug("DEBUG_MODE is True: Checking for default user...")
            default_exists = db.query(user.User).filter_by(username="default").first()
            if not default_exists:
                default_user = user.User(username="default")
                default_user.set_password("default_password")
                db.add(default_user)
                db.commit()
                logger.info("Created default user for DEBUG usage only")
            else:
                logger.debug("Default user already exists (DEBUG).")
        else:
            # In production, do not create any default user
            logger.info("Production mode: no default user created. Use /register to initialize.")

        # Fetch any existing user (default or otherwise)
        existing_user = db.query(user.User).first()
        if not existing_user:
            logger.info("No user found. Skipping default account creation.")
            db.close()
            logger.debug("Closed database session with no account creation")
            print("Database tables created successfully (no user yet).")
            return

        user_id = existing_user.id
        logger.debug(f"Found existing user with id={user_id}. Proceeding with account setup.")

        # Define the core accounts needed by the system
        all_accounts = [
            {"name": "Bank", "currency": "USD"},
            {"name": "Wallet", "currency": "BTC"},
            {"name": "Exchange USD", "currency": "USD"},
            {"name": "Exchange BTC", "currency": "BTC"},
            {"name": "BTC Fees", "currency": "BTC"},
            {"name": "USD Fees", "currency": "USD"}
        ]

        # Only create each account if it doesn't already exist
        for acct in all_accounts:
            existing_acct = db.query(account.Account).filter_by(name=acct["name"]).first()
            if not existing_acct:
                new_acct = account.Account(
                    user_id=user_id,
                    name=acct["name"],
                    currency=acct["currency"]
                )
                db.add(new_acct)
                logger.info(f"Created account '{acct['name']}' ({acct['currency']})")
        
        db.commit()
        logger.debug("Committed default accounts")

    except Exception as e:
        logger.error(f"Error during account initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        logger.debug("Closed database session in create_tables")

    print("Database tables created successfully.")
    logger.debug("Finished create_tables")
