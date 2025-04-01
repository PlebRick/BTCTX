# FILE: backend/tests/8949_multipage.py

import sys
import os
from decimal import Decimal
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.database import SessionLocal
from backend.models.account import Account
from backend.services.transaction import create_transaction_record

db = SessionLocal()

# Get accounts
exchange_usd = db.query(Account).filter_by(name="Exchange USD").first()
exchange_btc = db.query(Account).filter_by(name="Exchange BTC").first()

# Timestamp ranges
start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)

# --- Deposit 1M USD into Exchange USD
create_transaction_record({
    "type": "Deposit",
    "timestamp": start_date,
    "from_account_id": 99,
    "to_account_id": exchange_usd.id,
    "amount": Decimal("1000000.00"),
    "source": "Test Multipage USD"
}, db)

# --- Make 30 small BTC buys over time
for i in range(30):
    buy_time = start_date + timedelta(days=i + 1)
    btc_amount = Decimal("0.01")
    usd_cost = Decimal("300.00")  # pretend BTC price = $30,000

    create_transaction_record({
        "type": "Buy",
        "timestamp": buy_time,
        "from_account_id": exchange_usd.id,
        "to_account_id": exchange_btc.id,
        "amount": btc_amount,
        "cost_basis_usd": usd_cost,
        "fee_amount": Decimal("0.00"),
        "fee_currency": "USD"
    }, db)

# --- Sell each of them at a higher price later in the year
sell_time = datetime(2024, 12, 15, tzinfo=timezone.utc)

for i in range(30):
    create_transaction_record({
        "type": "Sell",
        "timestamp": sell_time + timedelta(minutes=i),
        "from_account_id": exchange_btc.id,
        "to_account_id": exchange_usd.id,
        "amount": Decimal("0.01"),
        "proceeds_usd": Decimal("500.00"),
        "fee_amount": Decimal("0.00"),
        "fee_currency": "USD"
    }, db)

print("✅ 30 Buys + 30 Sells inserted. Ready to trigger multi-page Form 8949.")
db.close()
