#!/usr/bin/env python
"""
backend/database.py

This module sets up the SQLAlchemy database connection, session management, and
provides helper functions for creating the database tables. It has been updated
to support the new double-entry system in BitcoinTX, where models (such as Transaction)
include both from_account_id and to_account_id.

Additionally, it loads environment variables from a .env file located at the project root,
ensuring that the database file and URL are correctly configured.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# -----------------------
# Environment Setup
# -----------------------
# Determine the base directory and project root.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Load environment variables from the .env file in the project root.
dotenv_path = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=dotenv_path)

# Get the database file path from the environment, defaulting to "backend/bitcoin_tracker.db".
DATABASE_FILE_ENV = os.getenv("DATABASE_FILE", "backend/bitcoin_tracker.db")

# Convert relative DB path to absolute.
if os.path.isabs(DATABASE_FILE_ENV):
    DATABASE_FILE = DATABASE_FILE_ENV
else:
    DATABASE_FILE = os.path.join(PROJECT_ROOT, DATABASE_FILE_ENV)

# Ensure the directory for the database exists.
db_dir = os.path.dirname(DATABASE_FILE)
if not os.path.exists(db_dir):
    os.makedirs(db_dir)
    print(f"Created directory for database: {db_dir}")

# Determine the DATABASE_URL from the environment, or default to a SQLite URL.
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_FILE}")
print("DATABASE_URL used:", DATABASE_URL)

# -----------------------
# SQLAlchemy Engine and Session Setup
# -----------------------
# Create the SQLAlchemy engine with the given DATABASE_URL.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create a session factory that will generate new Session objects.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for our ORM models.
Base = declarative_base()

# -----------------------
# Dependency for FastAPI
# -----------------------
def get_db():
    """
    Provide a database session for FastAPI routes or other components as a dependency.
    Yields a session and ensures it is closed after use, preventing resource leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------
# Helper Function: Create Tables
# -----------------------
def create_tables():
    """
    Create all database tables defined by the ORM models.
    
    This function imports the models (account, transaction, user, etc.) so that
    they are registered with Base.metadata. Then it calls create_all() on the engine
    to build the tables according to the latest schema.
    
    This is the function used by your create_db.py script.
    """
    print("Creating database tables...")
    try:
        # Import models to register them with Base.
        from backend.models import account, transaction, user
    except ImportError as e:
        print("Error importing models:", e)
        raise e

    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")
