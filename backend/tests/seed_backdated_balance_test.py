#!/usr/bin/env python3

import requests
from datetime import datetime, timedelta, timezone

BASE_URL = "http://127.0.0.1:8000"
DELETE_ALL = f"{BASE_URL}/api/transactions/delete_all"

EXTERNAL = 99
EXCHANGE_USD = 3
EXCHANGE_BTC = 4

def create(tx):
    r = requests.post(f"{BASE_URL}/api/transactions", json=tx)
    r.raise_for_status()
    return r.json()

def main():
    print("🧹 Deleting all transactions...")
    r = requests.delete(DELETE_ALL)
    if r.status_code not in (200, 204):
        print(f"❌ Failed to delete transactions: {r.status_code}")
        return

    print("➕ Seeding 2024 and 2025 transactions...")

    # Add some basic 2024 and 2025 activity
    dt_2024 = datetime(2024, 6, 1, tzinfo=timezone.utc)
    dt_2025 = datetime(2025, 6, 1, tzinfo=timezone.utc)

    create({
        "type": "Deposit",
        "timestamp": dt_2024.isoformat(),
        "from_account_id": EXTERNAL,
        "to_account_id": EXCHANGE_USD,
        "amount": "100000",
        "fee_amount": "0",
        "fee_currency": "USD",
        "source": "N/A"
    })

    create({
        "type": "Buy",
        "timestamp": (dt_2024 + timedelta(days=1)).isoformat(),
        "from_account_id": EXCHANGE_USD,
        "to_account_id": EXCHANGE_BTC,
        "amount": "1.0",
        "fee_amount": "10",
        "fee_currency": "USD",
        "cost_basis_usd": "30000"
    })

    create({
        "type": "Sell",
        "timestamp": dt_2025.isoformat(),
        "from_account_id": EXCHANGE_BTC,
        "to_account_id": EXCHANGE_USD,
        "amount": "0.5",
        "fee_amount": "5",
        "fee_currency": "USD",
        "proceeds_usd": "35000"
    })

    print("⏪ Seeding backdated 2023 transactions...")

    dt_2023 = datetime(2023, 1, 2, 12, 0, 0, tzinfo=timezone.utc)

    create({
        "type": "Deposit",
        "timestamp": dt_2023.isoformat(),
        "from_account_id": EXTERNAL,
        "to_account_id": EXCHANGE_USD,
        "amount": "15000",
        "fee_amount": "0",
        "fee_currency": "USD",
        "source": "N/A"
    })

    create({
        "type": "Buy",
        "timestamp": (dt_2023 + timedelta(hours=1)).isoformat(),
        "from_account_id": EXCHANGE_USD,
        "to_account_id": EXCHANGE_BTC,
        "amount": "0.25",
        "fee_amount": "5",
        "fee_currency": "USD",
        "cost_basis_usd": "6000"
    })

    create({
        "type": "Sell",
        "timestamp": datetime(2023, 12, 15, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
        "from_account_id": EXCHANGE_BTC,
        "to_account_id": EXCHANGE_USD,
        "amount": "0.25",
        "fee_amount": "10",
        "fee_currency": "USD",
        "proceeds_usd": "7000"
    })

    print("✅ Seeding complete! Run the report for 2023 in your frontend and confirm 'Beginning of Year Holdings' is 0 BTC.")

if __name__ == "__main__":
    main()
