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
wallet = db.query(Account).filter_by(name="Wallet").first()

# Timestamp anchors
long_term_start = datetime(2022, 1, 1, tzinfo=timezone.utc)
short_term_start = datetime(2024, 1, 1, tzinfo=timezone.utc)
sell_time = datetime(2024, 12, 15, tzinfo=timezone.utc)

# --- Deposits to fund buys
create_transaction_record({
    "type": "Deposit",
    "timestamp": long_term_start,
    "from_account_id": 99,
    "to_account_id": exchange_usd.id,
    "amount": Decimal("100000.00"),
    "source": "Test Edge Deposit"
}, db)

# --- Long-term buys (will go to Box D or F depending on flag)
for i in range(3):
    create_transaction_record({
        "type": "Buy",
        "timestamp": long_term_start + timedelta(days=i * 20),
        "from_account_id": exchange_usd.id,
        "to_account_id": exchange_btc.id,
        "amount": Decimal("0.1"),
        "cost_basis_usd": Decimal("2000.00"),
        "fee_amount": Decimal("1.00"),
        "fee_currency": "USD"
    }, db)

# --- Short-term buys
for i in range(3):
    create_transaction_record({
        "type": "Buy",
        "timestamp": short_term_start + timedelta(days=i * 10),
        "from_account_id": exchange_usd.id,
        "to_account_id": exchange_btc.id,
        "amount": Decimal("0.1"),
        "cost_basis_usd": Decimal("3000.00"),
        "fee_amount": Decimal("1.00"),
        "fee_currency": "USD"
    }, db)

# --- Sell (with proceeds) — some long, some short
for i in range(6):
    create_transaction_record({
        "type": "Sell",
        "timestamp": sell_time + timedelta(hours=i),
        "from_account_id": exchange_btc.id,
        "to_account_id": exchange_usd.id,
        "amount": Decimal("0.1"),
        "proceeds_usd": Decimal("5000.00"),
        "fee_amount": Decimal("2.00"),
        "fee_currency": "USD"
    }, db)

# --- Gift (no proceeds, FMV only)
create_transaction_record({
    "type": "Withdrawal",
    "timestamp": sell_time + timedelta(days=1),
    "from_account_id": exchange_btc.id,
    "to_account_id": 99,
    "amount": Decimal("0.05"),
    "purpose": "Gift",
    "fmv_usd": Decimal("2500.00"),
    "fee_amount": Decimal("0.00"),
    "fee_currency": "BTC"
}, db)

# --- Donation
create_transaction_record({
    "type": "Withdrawal",
    "timestamp": sell_time + timedelta(days=2),
    "from_account_id": exchange_btc.id,
    "to_account_id": 99,
    "amount": Decimal("0.05"),
    "purpose": "Donation",
    "fmv_usd": Decimal("2500.00"),
    "fee_amount": Decimal("0.00"),
    "fee_currency": "BTC"
}, db)

# --- Lost BTC
create_transaction_record({
    "type": "Withdrawal",
    "timestamp": sell_time + timedelta(days=3),
    "from_account_id": exchange_btc.id,
    "to_account_id": 99,
    "amount": Decimal("0.02"),
    "purpose": "Lost",
    "fmv_usd": Decimal("1000.00"),
    "fee_amount": Decimal("0.00"),
    "fee_currency": "BTC"
}, db)

# --- Transfer with BTC fee
create_transaction_record({
    "type": "Transfer",
    "timestamp": sell_time + timedelta(days=4),
    "from_account_id": exchange_btc.id,
    "to_account_id": wallet.id,
    "amount": Decimal("0.5"),
    "fee_amount": Decimal("0.001"),
    "fee_currency": "BTC"
}, db)

# --- Withdrawal with proceeds (Spent)
create_transaction_record({
    "type": "Withdrawal",
    "timestamp": sell_time + timedelta(days=5),
    "from_account_id": exchange_btc.id,
    "to_account_id": 99,
    "amount": Decimal("0.1"),
    "purpose": "Spent",
    "proceeds_usd": Decimal("4000.00"),
    "fee_amount": Decimal("1.00"),
    "fee_currency": "USD"
}, db)

# --- BTC income (Reward)
create_transaction_record({
    "type": "Deposit",
    "timestamp": sell_time + timedelta(days=6),
    "from_account_id": 99,
    "to_account_id": wallet.id,
    "amount": Decimal("0.03"),
    "source": "Reward",
    "cost_basis_usd": Decimal("1200.00")
}, db)

# --- USD income
create_transaction_record({
    "type": "Deposit",
    "timestamp": sell_time + timedelta(days=7),
    "from_account_id": 99,
    "to_account_id": exchange_usd.id,
    "amount": Decimal("500.00"),
    "source": "Interest"
}, db)

print("✅ Edge-case transactions inserted for full Form 8949 + Schedule D coverage.")
db.close()
