#!/usr/bin/env python3
"""
delete_users.py

Utility script to delete users from the BitcoinTX SQLite database.
Deletes all users unless a specific username or user_id is provided.

Usage:
  - Delete all users:
      python backend/scripts/delete_users.py

  - Delete user by username:
      python backend/scripts/delete_users.py --username myuser

  - Delete user by ID:
      python backend/scripts/delete_users.py --user_id 1
"""

import sys
import os
import argparse
from dotenv import load_dotenv

# Set up path to import backend modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from backend.database import SessionLocal, create_tables
from backend.models import user as user_model

# Load environment
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

def main():
    parser = argparse.ArgumentParser(description="Delete users from the BitcoinTX database.")
    parser.add_argument("--username", type=str, help="Delete user by username")
    parser.add_argument("--user_id", type=int, help="Delete user by ID")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.username:
            target_user = db.query(user_model.User).filter_by(username=args.username).first()
            if not target_user:
                print(f"No user found with username: {args.username}")
                return
            db.delete(target_user)
            db.commit()
            print(f"Deleted user '{args.username}' successfully.")
        elif args.user_id:
            target_user = db.query(user_model.User).filter_by(id=args.user_id).first()
            if not target_user:
                print(f"No user found with ID: {args.user_id}")
                return
            db.delete(target_user)
            db.commit()
            print(f"Deleted user with ID {args.user_id} successfully.")
        else:
            # Delete all users
            users = db.query(user_model.User).all()
            if not users:
                print("No users found.")
                return
            for u in users:
                print(f"Deleting user: {u.username} (ID {u.id})")
                db.delete(u)
            db.commit()
            print("All users deleted successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error deleting user(s): {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
