# database.py
# Sets up core database components for BitcoinTX, including engine, session management, and table creation logic.

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()

# --- Database URL Setup ---
# Database connection string; defaults to SQLite if not provided.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///backend/database.sqlite")

# --- Engine Setup ---
# SQLAlchemy engine manages the database connection.
# 'check_same_thread' is necessary for SQLite to allow multi-threaded operations.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# --- Session Setup ---
# Handles transactions with the database.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Base Class for ORM Models ---
# All models inherit from this base class.
Base = declarative_base()

# --- Table Creation Function ---
def create_tables():
    """
    Creates all database tables using the ORM models defined in the application.
    Ensure models are imported before running this function to avoid missing tables.
    """
    print("Creating database tables...")
    from backend.models import User, Account, Transaction  # Import models only when necessary to avoid circular dependencies
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

# --- Dependency for FastAPI ---
# Provides a database session dependency for FastAPI routes.
def get_db():
    """
    Dependency to yield a database session for FastAPI routes.
    Ensures that the session is properly closed after each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
