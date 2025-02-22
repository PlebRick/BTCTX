#!/usr/bin/env python
"""
create_account_db.py

1) Ensures database tables exist (via create_tables()).
2) Creates or finds a "testuser".
3) Creates four accounts for that user: Bank (USD), Wallet (BTC), ExchangeUSD, ExchangeBTC.
4) Seeds example deposit transactions from an external account (ID=99).
   Each deposit triggers the new double-entry logic, creating multiple LedgerEntry lines.

All references to "MyBTC" or "Income" are now stored simply as strings in the
Transaction model's 'source' field. We no longer rely on a TransactionSource enum.

Usage:
  python backend/create_account_db.py
"""

import sys
import os
from datetime import datetime
from decimal import Decimal

# --------------------------------------------------
# 1) Add project root to sys.path
# --------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    print(f"Project root added to sys.path: {PROJECT_ROOT}")
else:
    print(f"Project root already in sys.path: {PROJECT_ROOT}")

# --------------------------------------------------
# 2) Import relevant functions & classes
# --------------------------------------------------
try:
    # create_tables => sets up DB schema for double-entry (LedgerEntry, etc.)
    from backend.database import create_tables, SessionLocal

    # For user creation
    from backend.schemas.user import UserCreate
    from backend.services.user import create_user, get_user_by_username

    # For account creation
    from backend.schemas.account import AccountCreate
    from backend.services.account import create_account

    # For deposit transactions
    from backend.services.transaction import create_transaction_record

except ImportError as e:
    print("Error importing from backend:", e)
    sys.exit(1)


# --------------------------------------------------
# 3) Main function
# --------------------------------------------------
def main():
    """
    1) create_tables(): ensures the double-entry tables exist 
       (Transaction, LedgerEntry, BitcoinLot, LotDisposal, etc.).
    2) create/find 'testuser' in the DB.
    3) create four accounts for that user (Bank, Wallet, ExchangeUSD, ExchangeBTC).
    4) seed deposit transactions from an external account (ID=99).
       Each deposit triggers the multi-line logic in create_transaction_record:
         - Possibly creating LedgerEntry lines
         - Possibly creating a BitcoinLot if it's BTC
    """
    print("Creating database tables if they do not exist...")
    create_tables()  # calls backend.database -> Base.metadata.create_all()

    db = SessionLocal()
    try:
        # ------------------------------------------------
        # 1) Create or find user
        # ------------------------------------------------
        username = "testuser"
        user = get_user_by_username(username, db)
        if not user:
            # If user doesn't exist, create them
            user_data = UserCreate(username=username, password_hash="mysecretpass")
            user = create_user(user_data, db)
            print(f"Created new user: {user}")
        else:
            print(f"Found existing user (ID={user.id}): {user.username}")

        # ------------------------------------------------
        # 2) Create four accounts for that user
        # ------------------------------------------------
        user_id = user.id
        bank_acct = create_account(AccountCreate(
            user_id=user_id,
            name="Bank",
            currency="USD"
        ), db)
        wallet_acct = create_account(AccountCreate(
            user_id=user_id,
            name="Wallet",
            currency="BTC"
        ), db)
        exch_usd_acct = create_account(AccountCreate(
            user_id=user_id,
            name="ExchangeUSD",
            currency="USD"
        ), db)
        exch_btc_acct = create_account(AccountCreate(
            user_id=user_id,
            name="ExchangeBTC",
            currency="BTC"
        ), db)

        print(f"Accounts created for user {user_id}:")
        print(f"  Bank => {bank_acct.id}")
        print(f"  Wallet => {wallet_acct.id}")
        print(f"  ExchangeUSD => {exch_usd_acct.id}")
        print(f"  ExchangeBTC => {exch_btc_acct.id}")

        # ------------------------------------------------
        # 3) Seed deposit transactions from external=99
        # ------------------------------------------------
        # Example 1: USD deposit to Bank
        bank_deposit = {
            "from_account_id": 99,    # External
            "to_account_id": bank_acct.id,
            "type": "Deposit",
            "amount": Decimal("1000"),
            "timestamp": datetime.utcnow(),
            "fee_amount": Decimal("0.00"),
            "fee_currency": "USD",
            "source": "Income",       # For USD deposit, 'Income' is stored as a plain string
        }
        new_bank_tx = create_transaction_record(bank_deposit, db)

        # Example 2: BTC deposit to Wallet
        # We label the source as "MyBTC" (still a string, no enum).
        wallet_deposit = {
            "from_account_id": 99,
            "to_account_id": wallet_acct.id,
            "type": "Deposit",
            "amount": Decimal("0.5"),
            "timestamp": datetime.utcnow(),
            "fee_amount": Decimal("0.0001"),
            "fee_currency": "BTC",
            "source": "MyBTC",  # Plain string, no enum. 
            "cost_basis_usd": Decimal("12000")  # e.g., 0.5 BTC basis
        }
        new_wallet_tx = create_transaction_record(wallet_deposit, db)

        # Example 3: USD deposit to ExchangeUSD
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

        # Example 4: BTC deposit to ExchangeBTC
        exch_btc_deposit = {
            "from_account_id": 99,
            "to_account_id": exch_btc_acct.id,
            "type": "Deposit",
            "amount": Decimal("1.0"),
            "timestamp": datetime.utcnow(),
            "fee_amount": Decimal("0.0002"),
            "fee_currency": "BTC",
            "source": "MyBTC",  # Again, a string
            "cost_basis_usd": Decimal("24000")
        }
        new_ex_btc_tx = create_transaction_record(exch_btc_deposit, db)

        # Summaries
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

# --------------------------------------------------
# 4) Entry Point
# --------------------------------------------------
if __name__ == "__main__":
    main()
