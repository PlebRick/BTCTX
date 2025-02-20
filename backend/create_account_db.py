#!/usr/bin/env python
"""
create_account_db.py

Seeds the database with:
  1) One sample user (with hashed password).
  2) Four accounts (Bank=USD, Wallet=BTC, ExchangeUSD=USD, ExchangeBTC=BTC)
     linked to that user.
  3) Some "Deposit" transactions to give each account an initial balance,
     following the new double-entry model and single-amount approach.

Usage:
    From the project root, run:
        python -m backend.create_account_db
"""

import sys
import os
from datetime import datetime
from decimal import Decimal

# 1) Ensure PROJECT_ROOT is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    print(f"Project root added to sys.path: {PROJECT_ROOT}")

# 2) Import create_tables, DB session, and required models/services
try:
    from backend.database import create_tables, SessionLocal
except ImportError as e:
    print("Error importing from backend.database:", e)
    sys.exit(1)

try:
    # Import your user creation logic
    from backend.schemas.user import UserCreate
    from backend.services.user import create_user, get_user_by_username

    # Import account logic
    from backend.schemas.account import AccountCreate
    from backend.services.account import create_account

    # Import transaction logic
    from backend.services.transaction import create_transaction_record
except ImportError as e:
    print("Error importing models/services/schemas:", e)
    sys.exit(1)


def main():
    """
    1) Create all tables (if not existing).
    2) Insert a test user with a hashed password.
    3) Create four accounts for that user (Bank, Wallet, ExchangeUSD, ExchangeBTC).
    4) Seed each account with an initial 'Deposit' transaction from External=99.
    """
    print("Creating all tables if they do not exist...")
    create_tables()

    db = SessionLocal()
    try:
        # --------------------------------------------------------------------
        # 1) Create or find a test user
        #    "UserCreate" expects a plain-text password in the "password_hash" field.
        #    We will pass "mysecretpass" as an example. The user model will re-hash it.
        # --------------------------------------------------------------------
        username = "testuser"
        existing_user = get_user_by_username(username, db)
        if existing_user:
            print(f"User '{username}' already exists. Using that user.")
            user = existing_user
        else:
            user_data = UserCreate(
                username=username,
                password_hash="mysecretpass"  # Plain text that gets hashed by set_password
            )
            user = create_user(user_data, db)
            if not user:
                raise ValueError("Failed to create new test user.")
            print(f"Created new user (ID={user.id}, username={user.username}).")

        # --------------------------------------------------------------------
        # 2) Create some accounts for that user
        #    We'll use the 'create_account' service function,
        #    passing an AccountCreate dict. We also must ensure 'user_id' is set!
        # --------------------------------------------------------------------
        bank_data = AccountCreate(name="Bank", currency="USD")
        wallet_data = AccountCreate(name="Wallet", currency="BTC")
        exchange_usd_data = AccountCreate(name="ExchangeUSD", currency="USD")
        exchange_btc_data = AccountCreate(name="ExchangeBTC", currency="BTC")

        # We need to add user_id to each AccountCreate if your account model requires it
        # (Check your account model for a user_id = Column(ForeignKey('users.id'))
        # If so, let's add that:
        bank_data_dict = bank_data.dict()
        bank_data_dict["user_id"] = user.id

        wallet_data_dict = wallet_data.dict()
        wallet_data_dict["user_id"] = user.id

        exchange_usd_data_dict = exchange_usd_data.dict()
        exchange_usd_data_dict["user_id"] = user.id

        exchange_btc_data_dict = exchange_btc_data.dict()
        exchange_btc_data_dict["user_id"] = user.id

        # Create each account
        bank_acct = create_account(bank_data_dict, db)
        wallet_acct = create_account(wallet_data_dict, db)
        exch_usd_acct = create_account(exchange_usd_data_dict, db)
        exch_btc_acct = create_account(exchange_btc_data_dict, db)

        print(f"Created accounts (IDs):")
        print(f"  Bank => {bank_acct.id} (USD)")
        print(f"  Wallet => {wallet_acct.id} (BTC)")
        print(f"  ExchangeUSD => {exch_usd_acct.id} (USD)")
        print(f"  ExchangeBTC => {exch_btc_acct.id} (BTC)")

        # --------------------------------------------------------------------
        # 3) Seed balances with 'Deposit' transactions from External=99
        # --------------------------------------------------------------------

        # 3a) Deposit $1000 to Bank
        tx_data_bank = {
            "from_account_id": 99,   # External
            "to_account_id": bank_acct.id,
            "type": "Deposit",
            "amount": Decimal("1000.00"),
            "timestamp": datetime.utcnow(),
            "fee_amount": Decimal("0.00"),
            "fee_currency": "USD",
            "source": "Income",  # For USD deposit, not strictly necessary
        }
        new_bank_tx = create_transaction_record(tx_data_bank, db)

        # 3b) Deposit 0.5 BTC to Wallet (with cost basis)
        tx_data_wallet = {
            "from_account_id": 99,
            "to_account_id": wallet_acct.id,
            "type": "Deposit",
            "amount": Decimal("0.5"),
            "timestamp": datetime.utcnow(),
            "fee_amount": Decimal("0.0001"),
            "fee_currency": "BTC",
            "source": "My BTC",
            "cost_basis_usd": Decimal("12000.00"),  # e.g. 0.5 BTC was worth $12k total
        }
        new_wallet_tx = create_transaction_record(tx_data_wallet, db)

        # 3c) Deposit $500 to ExchangeUSD
        tx_data_exch_usd = {
            "from_account_id": 99,
            "to_account_id": exch_usd_acct.id,
            "type": "Deposit",
            "amount": Decimal("500.00"),
            "timestamp": datetime.utcnow(),
            "fee_amount": Decimal("0.00"),
            "fee_currency": "USD",
            "source": "Income",
        }
        new_ex_usd_tx = create_transaction_record(tx_data_exch_usd, db)

        # 3d) Deposit 1.0 BTC to ExchangeBTC (with cost basis)
        tx_data_exch_btc = {
            "from_account_id": 99,
            "to_account_id": exch_btc_acct.id,
            "type": "Deposit",
            "amount": Decimal("1.0"),
            "timestamp": datetime.utcnow(),
            "fee_amount": Decimal("0.0002"),
            "fee_currency": "BTC",
            "source": "My BTC",
            "cost_basis_usd": Decimal("24000.00"),
        }
        new_ex_btc_tx = create_transaction_record(tx_data_exch_btc, db)

        print("All seed data inserted successfully!")
        print(f"  Bank deposit TX => ID={new_bank_tx.id}")
        print(f"  Wallet deposit TX => ID={new_wallet_tx.id}")
        print(f"  ExchangeUSD deposit TX => ID={new_ex_usd_tx.id}")
        print(f"  ExchangeBTC deposit TX => ID={new_ex_btc_tx.id}")

    except Exception as e:
        db.rollback()
        print("Error while seeding data:", e)
    finally:
        db.close()


if __name__ == "__main__":
    main()
