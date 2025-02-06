#!/usr/bin/env python
"""
database.py

This module sets up the core database components for BitcoinTX:
- Loads environment variables from the .env file (located in the project root).
- Determines an absolute path for the SQLite database file using a relative path from the .env.
- Creates the SQLAlchemy engine, session factory, and ORM Base.
- Provides functions to create database tables and a FastAPI dependency for obtaining a database session.

Best Practices:
- Place the .env file in the project root for portability.
- Use relative paths in configuration files and convert them to absolute paths in code.
- Do not hard-code user-specific paths.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from the .env file located in the project root.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # This is the backend folder.
PROJECT_ROOT = os.path.dirname(BASE_DIR)
dotenv_path = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=dotenv_path)

# Retrieve DATABASE_FILE from the environment; default to a relative path.
DATABASE_FILE_ENV = os.getenv("DATABASE_FILE", "backend/bitcoin_tracker.db")

# Convert to an absolute path: if DATABASE_FILE_ENV is relative, join it with PROJECT_ROOT.
if os.path.isabs(DATABASE_FILE_ENV):
    DATABASE_FILE = DATABASE_FILE_ENV
else:
    DATABASE_FILE = os.path.join(PROJECT_ROOT, DATABASE_FILE_ENV)

# Ensure the directory for the database file exists.
db_dir = os.path.dirname(DATABASE_FILE)
if not os.path.exists(db_dir):
    os.makedirs(db_dir)
    print(f"Created directory for database: {db_dir}")

# Build the full DATABASE_URL.
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_FILE}")

# Debug: Print the DATABASE_URL.
print("DATABASE_URL used:", DATABASE_URL)

# Create the SQLAlchemy engine.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a session factory.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the Base class for ORM models.
Base = declarative_base()

def create_tables():
    """
    Create all database tables defined by the ORM models.

    This function imports all models (e.g., account, transaction, user)
    so that their table definitions are registered with Base.metadata.
    Then, it creates the tables in the database using the configured engine.
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
    Provide a database session for FastAPI routes as a dependency.

    Yields:
        Session: A SQLAlchemy session for performing database operations.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
