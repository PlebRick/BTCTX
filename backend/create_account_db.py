#!/usr/bin/env python
"""
create_account_db.py

A script to seed the database with:
  - One sample user
  - Four accounts (Bank=USD, Wallet=BTC, ExchangeUSD=USD, ExchangeBTC=BTC)
  - A few deposit transactions to give each account a starting balance.

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

# 2) Import create_tables and DB session
try:
    from backend.database import create_tables, SessionLocal
except ImportError as e:
    print("Error importing from backend.database:", e)
    sys.exit(1)

# 3) Import models & services
# If you have a backend.models.user, adjust accordingly
try:
    from backend.models.user import User
    from backend.services.account import create_account
    from backend.services.transaction import create_transaction_record
except ImportError as e:
    print("Error importing models/services:", e)
    sys.exit(1)

def main():
    """
    1) Create all tables.
    2) Insert a test user.
    3) Create four accounts (Bank, Wallet, ExchangeUSD, ExchangeBTC).
    4) Perform deposit transactions to seed balances.
    """
    print("Creating all tables (if not existing)...")
    create_tables()

    db = SessionLocal()
    try:
        # 1) Create or find a test user
        #    If your system doesn't require a user, omit this.
        user = User(username="testuser", email="test@example.com")
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created test user (ID={user.id}).")

        # 2) Create some accounts for that user
        #    We'll use the 'create_account' service function
        #    that expects an AccountCreate schema-like object.
        bank_data = {"name": "Bank", "currency": "USD"}
        wallet_data = {"name": "Wallet", "currency": "BTC"}
        exchange_usd_data = {"name": "ExchangeUSD", "currency": "USD"}
        exchange_btc_data = {"name": "ExchangeBTC", "currency": "BTC"}

        # Create each account
        bank_acct = create_account(bank_data, db)
        wallet_acct = create_account(wallet_data, db)
        exch_usd_acct = create_account(exchange_usd_data, db)
        exch_btc_acct = create_account(exchange_btc_data, db)

        print(f"Created accounts (IDs): Bank={bank_acct.id}, "
              f"Wallet={wallet_acct.id}, ExchangeUSD={exch_usd_acct.id}, ExchangeBTC={exch_btc_acct.id}")

        # 3) Seed some balances with 'Deposit' transactions
        #    Because we have a single `amount` field, we do e.g. 1000 USD to Bank, 0.5 BTC to Wallet, etc.
        #    from_account_id = 99 => "External"
        #    to_account_id   = bank_acct.id => deposit to Bank
        #    type = 'Deposit', amount in the account's currency

        # Deposit 1000 USD into Bank
        tx_data_bank = {
            "from_account_id": 99,    # External
            "to_account_id": bank_acct.id,
            "type": "Deposit",
            "amount": Decimal("1000.00"),
            "timestamp": datetime.utcnow(),
            "fee_amount": Decimal("0.00"),
            "fee_currency": "USD",
            "source": "Income",      # For BTC deposit, you'd track cost_basis, but here it's USD
            "is_locked": False
        }
        new_bank_tx = create_transaction_record(tx_data_bank, db)

        # Deposit 0.5 BTC into Wallet
        tx_data_wallet = {
            "from_account_id": 99,     # External
            "to_account_id": wallet_acct.id,
            "type": "Deposit",
            "amount": Decimal("0.5"),
            "timestamp": datetime.utcnow(),
            "fee_amount": Decimal("0.0001"),
            "fee_currency": "BTC",
            "source": "My BTC",       # BTC deposit
            "cost_basis_usd": Decimal("12000.00"),  # If we consider 0.5 BTC worth $12k total
            "is_locked": False
        }
        new_wallet_tx = create_transaction_record(tx_data_wallet, db)

        # Deposit 500 USD into ExchangeUSD
        tx_data_exch_usd = {
            "from_account_id": 99,
            "to_account_id": exch_usd_acct.id,
            "type": "Deposit",
            "amount": Decimal("500.00"),
            "timestamp": datetime.utcnow(),
            "fee_amount": Decimal("0.00"),
            "fee_currency": "USD",
            "source": "Income",
            "is_locked": False
        }
        new_ex_usd_tx = create_transaction_record(tx_data_exch_usd, db)

        # Deposit 1.0 BTC into ExchangeBTC
        tx_data_exch_btc = {
            "from_account_id": 99,
            "to_account_id": exch_btc_acct.id,
            "type": "Deposit",
            "amount": Decimal("1.0"),
            "timestamp": datetime.utcnow(),
            "fee_amount": Decimal("0.0002"),
            "fee_currency": "BTC",
            "source": "My BTC",
            "cost_basis_usd": Decimal("24000.00"),  # for 1 BTC
            "is_locked": False
        }
        new_ex_btc_tx = create_transaction_record(tx_data_exch_btc, db)

        print("Seed data created successfully!")
        print(f"Bank deposit TX ID = {new_bank_tx.id}")
        print(f"Wallet deposit TX ID = {new_wallet_tx.id}")
        print(f"ExchangeUSD deposit TX ID = {new_ex_usd_tx.id}")
        print(f"ExchangeBTC deposit TX ID = {new_ex_btc_tx.id}")

    except Exception as e:
        db.rollback()
        print("Error while seeding data:", e)
    finally:
        db.close()


if __name__ == "__main__":
    main()
