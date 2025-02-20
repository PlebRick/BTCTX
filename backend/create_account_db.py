#!/usr/bin/env python
"""
create_account_db.py

A minimal script to:
1. Create tables if missing.
2. Create/find a user (username="testuser").
3. Create four accounts linked to that user.
4. Seed deposit transactions (from External=99).

Uses the refactored 'test4' code where:
 - AccountCreate requires user_id
 - Transaction enums use "My BTC" (with space).

Usage:
  python -m backend.create_account_db
"""

import sys
import os
from datetime import datetime
from decimal import Decimal

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from backend.database import create_tables, SessionLocal
    from backend.schemas.user import UserCreate
    from backend.services.user import create_user, get_user_by_username
    from backend.schemas.account import AccountCreate
    from backend.services.account import create_account
    from backend.services.transaction import create_transaction_record
except ImportError as e:
    print("Error importing from backend:", e)
    sys.exit(1)

def main():
    print("Creating database tables if they do not exist...")
    create_tables()

    db = SessionLocal()
    try:
        # 1) Create/find user
        username = "testuser"
        user = get_user_by_username(username, db)
        if not user:
            # If user doesn't exist, create them
            user_data = UserCreate(username=username, password_hash="mysecretpass")
            user = create_user(user_data, db)
            print(f"Created new user: {user}")
        else:
            print(f"Found existing user (ID={user.id}): {user.username}")

        # 2) Create accounts for user
        user_id = user.id
        bank_acct = create_account(AccountCreate(user_id=user_id, name="Bank", currency="USD"), db)
        wallet_acct = create_account(AccountCreate(user_id=user_id, name="Wallet", currency="BTC"), db)
        exch_usd_acct = create_account(AccountCreate(user_id=user_id, name="ExchangeUSD", currency="USD"), db)
        exch_btc_acct = create_account(AccountCreate(user_id=user_id, name="ExchangeBTC", currency="BTC"), db)

        print(f"Accounts created for user {user_id}:")
        print(f"  Bank => {bank_acct.id}")
        print(f"  Wallet => {wallet_acct.id}")
        print(f"  ExchangeUSD => {exch_usd_acct.id}")
        print(f"  ExchangeBTC => {exch_btc_acct.id}")

        # 3) Seed deposit transactions from External=99
        bank_deposit = {
            "from_account_id": 99,   # External
            "to_account_id": bank_acct.id,
            "type": "Deposit",
            "amount": Decimal("1000"),
            "timestamp": datetime.utcnow(),
            "fee_amount": Decimal("0.00"),
            "fee_currency": "USD",
            "source": "Income"  # For USD deposit, just an example
        }
        new_bank_tx = create_transaction_record(bank_deposit, db)

        wallet_deposit = {
            "from_account_id": 99,
            "to_account_id": wallet_acct.id,
            "type": "Deposit",
            "amount": Decimal("0.5"),
            "timestamp": datetime.utcnow(),
            "fee_amount": Decimal("0.0001"),
            "fee_currency": "BTC",
            "source": "My BTC",             # Spaced version
            "cost_basis_usd": Decimal("12000")  # e.g. 0.5 BTC total basis
        }
        new_wallet_tx = create_transaction_record(wallet_deposit, db)

        exch_usd_deposit = {
            "from_account_id": 99,
            "to_account_id": exch_usd_acct.id,
            "type": "Deposit",
            "amount": Decimal("500"),
            "timestamp": datetime.utcnow(),
            "fee_amount": Decimal("0"),
            "fee_currency": "USD",
            "source": "Income"
        }
        new_ex_usd_tx = create_transaction_record(exch_usd_deposit, db)

        exch_btc_deposit = {
            "from_account_id": 99,
            "to_account_id": exch_btc_acct.id,
            "type": "Deposit",
            "amount": Decimal("1.0"),
            "timestamp": datetime.utcnow(),
            "fee_amount": Decimal("0.0002"),
            "fee_currency": "BTC",
            "source": "My BTC",            # Spaced version
            "cost_basis_usd": Decimal("24000")
        }
        new_ex_btc_tx = create_transaction_record(exch_btc_deposit, db)

        print("Seed deposits completed:")
        print(f"  Bank TX => {new_bank_tx.id}")
        print(f"  Wallet TX => {new_wallet_tx.id}")
        print(f"  ExchangeUSD TX => {new_ex_usd_tx.id}")
        print(f"  ExchangeBTC TX => {new_ex_btc_tx.id}")

    except Exception as e:
        db.rollback()
        print("Error while seeding data:", e)
    finally:
        db.close()

if __name__ == "__main__":
    main()
