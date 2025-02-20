#!/usr/bin/env python
"""
create_account_db.py

Seeds the database with:
  1) One sample user (with hashed password).
  2) Four accounts (Bank=USD, Wallet=BTC, ExchangeUSD=USD, ExchangeBTC=BTC)
     linked to that user via user_id.
  3) Some "Deposit" transactions to give each account an initial balance.

Usage:
    From the project root, run:
        python -m backend.create_account_db
"""

import sys
import os
from datetime import datetime
from decimal import Decimal

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    print(f"Project root added to sys.path: {PROJECT_ROOT}")

try:
    from backend.database import create_tables, SessionLocal
    # User / Account / Transaction logic
    from backend.schemas.user import UserCreate
    from backend.services.user import create_user, get_user_by_username
    from backend.schemas.account import AccountCreate
    from backend.services.account import create_account
    from backend.services.transaction import create_transaction_record
except ImportError as e:
    print("Error importing from backend:", e)
    sys.exit(1)


def main():
    """
    1) Create all tables if they don't exist.
    2) Insert a test user with a hashed password.
    3) Create four accounts for that user.
    4) Seed each account with an initial 'Deposit' transaction (from External=99).
    """
    print("Creating all tables if they do not exist...")
    create_tables()

    db = SessionLocal()
    try:
        # -------------------------------------------
        # 1) Create or find a test user
        # -------------------------------------------
        username = "testuser"
        existing_user = get_user_by_username(username, db)
        if existing_user:
            print(f"User '{username}' already exists. Using that user (ID={existing_user.id}).")
            user = existing_user
        else:
            user_data = UserCreate(
                username=username,
                password_hash="mysecretpass"  # will be hashed by set_password()
            )
            user = create_user(user_data, db)
            if not user:
                raise ValueError("Failed to create new test user.")
            print(f"Created new user (ID={user.id}, username={user.username}).")

        # -------------------------------------------
        # 2) Create some accounts for that user
        # -------------------------------------------
        # We have 4 base accounts: Bank(USD), Wallet(BTC), ExchangeUSD(USD), ExchangeBTC(BTC)

        # We'll define them as AccountCreate objects
        bank_data = AccountCreate(name="Bank", currency="USD")
        wallet_data = AccountCreate(name="Wallet", currency="BTC")
        exchange_usd_data = AccountCreate(name="ExchangeUSD", currency="USD")
        exchange_btc_data = AccountCreate(name="ExchangeBTC", currency="BTC")

        # Each model_dump() yields a dict, to which we add user_id
        # then reconstruct a new AccountCreate(**dict_with_user_id).
        bank_dict = bank_data.model_dump()
        bank_dict["user_id"] = user.id
        bank_acct_obj = AccountCreate(**bank_dict)
        bank_acct = create_account(bank_acct_obj, db)

        wallet_dict = wallet_data.model_dump()
        wallet_dict["user_id"] = user.id
        wallet_acct_obj = AccountCreate(**wallet_dict)
        wallet_acct = create_account(wallet_acct_obj, db)

        exch_usd_dict = exchange_usd_data.model_dump()
        exch_usd_dict["user_id"] = user.id
        exch_usd_acct_obj = AccountCreate(**exch_usd_dict)
        exch_usd_acct = create_account(exch_usd_acct_obj, db)

        exch_btc_dict = exchange_btc_data.model_dump()
        exch_btc_dict["user_id"] = user.id
        exch_btc_acct_obj = AccountCreate(**exch_btc_dict)
        exch_btc_acct = create_account(exch_btc_acct_obj, db)

        print("Created accounts:")
        print(f"  Bank (id={bank_acct.id}, currency={bank_acct.currency})")
        print(f"  Wallet (id={wallet_acct.id}, currency={wallet_acct.currency})")
        print(f"  ExchangeUSD (id={exch_usd_acct.id}, currency={exch_usd_acct.currency})")
        print(f"  ExchangeBTC (id={exch_btc_acct.id}, currency={exch_btc_acct.currency})")

        # -------------------------------------------
        # 3) Seed balances with 'Deposit' transactions from External=99
        # -------------------------------------------
        # 3a) Bank deposit
        tx_data_bank = {
            "from_account_id": 99,   # External
            "to_account_id": bank_acct.id,
            "type": "Deposit",
            "amount": Decimal("1000.00"),
            "timestamp": datetime.utcnow(),
            "fee_amount": Decimal("0.00"),
            "fee_currency": "USD",
            "source": "Income",
        }
        new_bank_tx = create_transaction_record(tx_data_bank, db)

        # 3b) Wallet deposit (BTC)
        tx_data_wallet = {
            "from_account_id": 99,
            "to_account_id": wallet_acct.id,
            "type": "Deposit",
            "amount": Decimal("0.5"),
            "timestamp": datetime.utcnow(),
            "fee_amount": Decimal("0.0001"),
            "fee_currency": "BTC",
            "source": "My BTC",
            "cost_basis_usd": Decimal("12000.00"),  # e.g. 0.5 BTC total basis
        }
        new_wallet_tx = create_transaction_record(tx_data_wallet, db)

        # 3c) ExchangeUSD deposit
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

        # 3d) ExchangeBTC deposit
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

        print("\nSeeding complete. Created deposit transactions:")
        print(f"  Bank TX => ID={new_bank_tx.id}")
        print(f"  Wallet TX => ID={new_wallet_tx.id}")
        print(f"  ExchangeUSD TX => ID={new_ex_usd_tx.id}")
        print(f"  ExchangeBTC TX => ID={new_ex_btc_tx.id}")

    except Exception as e:
        db.rollback()
        print("Error while seeding data:", e)
    finally:
        db.close()


if __name__ == "__main__":
    main()
