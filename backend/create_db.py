# create_db.py
# Initialize the database tables.

if __name__ == "__main__":
    import sys
    import os

    # Ensure the project root is in the Python path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from backend.database import create_tables

    # Create tables
    create_tables()