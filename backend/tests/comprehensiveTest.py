#!/usr/bin/env python3

"""
comprehensiveTest.py

A thorough end-to-end script to test BitcoinTX with a "scorched earth" approach.

Steps:
 1) DELETE all existing transactions via /api/transactions/delete_all.
 2) Create a wide range of transactions spanning 2 years.
 3) Update (edit) some existing transactions (e.g. cost_basis, timestamp).
 4) Dump all debug endpoints to verify final results.

You'll need these endpoints:
    - DELETE /api/transactions/delete_all
    - POST   /api/transactions
    - PUT    /api/transactions/{id}
    - GET    /api/transactions
    - GET    /api/debug/lots
    - GET    /api/debug/disposals
    - GET    /api/debug/ledger-entries
    - GET    /api/calculations/accounts/balances
    - GET    /api/calculations/gains-and-losses
    - GET    /api/calculations/average-cost-basis

Adjust BASE_URL, account IDs, etc., as needed.
"""

import requests
from datetime import datetime, timedelta, timezone

# --------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------
BASE_URL = "http://127.0.0.1:8000"  # Adjust if your API runs elsewhere

# The custom route you mentioned:
DELETE_ALL_ENDPOINT = f"{BASE_URL}/api/transactions/delete_all"

# If you need different account IDs, adjust these:
BANK_ID       = 1  # USD
WALLET_ID     = 2  # BTC
EXCHANGE_USD  = 3  # USD
EXCHANGE_BTC  = 4  # BTC
BTC_FEES      = 5
USD_FEES      = 6
EXTERNAL      = 99


# --------------------------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------------------------
def delete_all_transactions():
    """Delete all transactions by calling DELETE /api/transactions/delete_all."""
    print("Deleting all existing transactions...")
    resp = requests.delete(DELETE_ALL_ENDPOINT)
    if resp.status_code == 200:
        print("All transactions cleared successfully.\n")
    else:
        print(f"Warning: Unexpected status when deleting transactions: {resp.status_code}, {resp.text}")

def create_transaction(tx_data: dict) -> dict:
    """
    Create a transaction by POSTing to /api/transactions.
    Returns the created transaction JSON if successful.
    """
    url = f"{BASE_URL}/api/transactions"
    resp = requests.post(url, json=tx_data)
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"ERROR creating transaction with data={tx_data}")
        print(f"Status code: {resp.status_code}, Response: {resp.text}")
        raise e
    return resp.json()

def update_transaction(tx_id: int, updates: dict) -> dict:
    """Update an existing transaction (PUT /api/transactions/{tx_id})."""
    url = f"{BASE_URL}/api/transactions/{tx_id}"
    resp = requests.put(url, json=updates)
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"ERROR updating transaction #{tx_id} with updates={updates}")
        print(f"Status code: {resp.status_code}, Response: {resp.text}")
        raise e
    return resp.json()

def dump_all():
    """
    Dump all relevant endpoints for debugging:
      /api/transactions
      /api/debug/lots
      /api/debug/disposals
      /api/debug/ledger-entries
      /api/calculations/accounts/balances
      /api/calculations/gains-and-losses
      /api/calculations/average-cost-basis
    """
    endpoints = [
        "/api/transactions",
        "/api/debug/lots",
        "/api/debug/disposals",
        "/api/debug/ledger-entries",
        "/api/calculations/accounts/balances",
        "/api/calculations/gains-and-losses",
        "/api/calculations/average-cost-basis",
    ]
    for ep in endpoints:
        url = f"{BASE_URL}{ep}"
        print(f"----- GET {ep} -----")
        r = requests.get(url)
        if r.status_code == 200:
            print(r.json())
        else:
            print(f"[{r.status_code}] {r.text}")
        print()

# --------------------------------------------------------------------
# MAIN SCRIPT
# --------------------------------------------------------------------
def main():
    # 1) DELETE ALL
    delete_all_transactions()

    print("Posting new transactions in chronological order...\n")

    # We'll start from 2024-01-02T10:00:00Z
    base_dt = datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc)

    # Transaction #1: Deposit 1 BTC => WALLET (cost_basis=18000)
    tx1_data = {
        "type": "Deposit",
        "timestamp": base_dt.isoformat(),
        "from_account_id": EXTERNAL,
        "to_account_id": WALLET_ID,
        "amount": "1.0",
        "fee_amount": "0",
        "fee_currency": "BTC",
        "source": "Income",
        "cost_basis_usd": "18000",
    }
    tx1 = create_transaction(tx1_data)
    print(f"1) Created Deposit TX ID={tx1['id']} at {tx1['timestamp']}")

    # Transaction #2: Deposit 6000 USD => EXCHANGE_USD
    tx2_data = {
        "type": "Deposit",
        "timestamp": (base_dt + timedelta(days=1)).isoformat(),
        "from_account_id": EXTERNAL,
        "to_account_id": EXCHANGE_USD,
        "amount": "6000",
        "fee_amount": "0",
        "fee_currency": "USD",
        "source": "N/A",
    }
    tx2 = create_transaction(tx2_data)
    print(f"2) Created Deposit TX ID={tx2['id']} at {tx2['timestamp']}")

    # Transaction #3: Transfer 0.5 BTC => from WALLET => EXCHANGE_BTC, fee=0.0001
    tx3_data = {
        "type": "Transfer",
        "timestamp": (base_dt + timedelta(days=2, hours=2)).isoformat(),
        "from_account_id": WALLET_ID,
        "to_account_id": EXCHANGE_BTC,
        "amount": "0.5",
        "fee_amount": "0.0001",
        "fee_currency": "BTC",
    }
    tx3 = create_transaction(tx3_data)
    print(f"3) Created Transfer TX ID={tx3['id']} at {tx3['timestamp']}")

    # Transaction #4: Buy 0.2 BTC => from EXCHANGE_USD => EXCHANGE_BTC, cost_basis=4000, fee=50
    tx4_data = {
        "type": "Buy",
        "timestamp": (base_dt + timedelta(days=15)).isoformat(),
        "from_account_id": EXCHANGE_USD,
        "to_account_id": EXCHANGE_BTC,
        "amount": "0.2",
        "fee_amount": "50",
        "fee_currency": "USD",
        "cost_basis_usd": "4000",
    }
    tx4 = create_transaction(tx4_data)
    print(f"4) Created Buy TX ID={tx4['id']} at {tx4['timestamp']}")

    # Transaction #5: Deposit 2 BTC => WALLET, cost_basis=60000
    tx5_data = {
        "type": "Deposit",
        "timestamp": (base_dt + timedelta(days=30)).isoformat(),
        "from_account_id": EXTERNAL,
        "to_account_id": WALLET_ID,
        "amount": "2.0",
        "fee_amount": "0",
        "fee_currency": "BTC",
        "cost_basis_usd": "60000",
        "source": "Income",
    }
    tx5 = create_transaction(tx5_data)
    print(f"5) Created Deposit TX ID={tx5['id']} at {tx5['timestamp']}")

    # Transaction #6: Sell 0.3 BTC => from EXCHANGE_BTC => EXCHANGE_USD (proceeds=7000, fee=100)
    tx6_data = {
        "type": "Sell",
        "timestamp": (base_dt + timedelta(days=60)).isoformat(),
        "from_account_id": EXCHANGE_BTC,
        "to_account_id": EXCHANGE_USD,
        "amount": "0.3",
        "fee_amount": "100",
        "fee_currency": "USD",
        "proceeds_usd": "7000",
    }
    tx6 = create_transaction(tx6_data)
    print(f"6) Created Sell TX ID={tx6['id']} at {tx6['timestamp']}")

    # Transaction #7: ~1 year later, withdrawal 1 BTC from WALLET => external, fee=0.0002
    tx7_dt = base_dt + timedelta(days=365)
    tx7_data = {
        "type": "Withdrawal",
        "timestamp": tx7_dt.isoformat(),
        "from_account_id": WALLET_ID,
        "to_account_id": EXTERNAL,
        "amount": "1.0",
        "fee_amount": "0.0002",
        "fee_currency": "BTC",
        "purpose": "Spent",
    }
    tx7 = create_transaction(tx7_data)
    print(f"7) Created Withdrawal TX ID={tx7['id']} at {tx7['timestamp']}")

    # Transaction #8: Another deposit of 10000 USD => EXCHANGE_USD
    tx8_data = {
        "type": "Deposit",
        "timestamp": (tx7_dt + timedelta(days=1)).isoformat(),
        "from_account_id": EXTERNAL,
        "to_account_id": EXCHANGE_USD,
        "amount": "10000",
        "fee_amount": "0",
        "fee_currency": "USD",
    }
    tx8 = create_transaction(tx8_data)
    print(f"8) Created Deposit TX ID={tx8['id']} at {tx8['timestamp']}")

    # Transaction #9: Buy 1.0 BTC => from EXCHANGE_USD => EXCHANGE_BTC, cost_basis=25000, fee=200
    tx9_data = {
        "type": "Buy",
        "timestamp": (tx7_dt + timedelta(days=2)).isoformat(),
        "from_account_id": EXCHANGE_USD,
        "to_account_id": EXCHANGE_BTC,
        "amount": "1.0",
        "fee_amount": "200",
        "fee_currency": "USD",
        "cost_basis_usd": "25000",
    }
    tx9 = create_transaction(tx9_data)
    print(f"9) Created Buy TX ID={tx9['id']} at {tx9['timestamp']}")

    # Transaction #10: Sell 0.2 BTC => from EXCHANGE_BTC => EXCHANGE_USD, proceeds=6000, fee=50
    tx10_data = {
        "type": "Sell",
        "timestamp": (tx7_dt + timedelta(days=10)).isoformat(),
        "from_account_id": EXCHANGE_BTC,
        "to_account_id": EXCHANGE_USD,
        "amount": "0.2",
        "fee_amount": "50",
        "fee_currency": "USD",
        "proceeds_usd": "6000",
    }
    tx10 = create_transaction(tx10_data)
    print(f"10) Created Sell TX ID={tx10['id']} at {tx10['timestamp']}")

    print("\nAll base transactions created successfully.\n")

    # 3) Let's do some random updates
    print("Updating a couple transactions...\n")

    # Update #1: Backdate TX #5 by 3 days & reduce cost basis from 60000 => 55000
    new_ts_5 = (base_dt + timedelta(days=27)).isoformat()
    tx5_updates = {
        "timestamp": new_ts_5,
        "cost_basis_usd": "55000"
    }
    updated_tx5 = update_transaction(tx5["id"], tx5_updates)
    print(f"Updated TX #5 => new timestamp={updated_tx5['timestamp']}, cost_basis_usd={updated_tx5['cost_basis_usd']}")

    # Update #2: Increase TX #2 deposit from 6000 => 6500
    tx2_updates = {
        "amount": "6500.0"
    }
    updated_tx2 = update_transaction(tx2["id"], tx2_updates)
    print(f"Updated TX #2 => new amount={updated_tx2['amount']}")

    # 4) Dump everything
    print("\nDumping all debug endpoints to verify final calculations...\n")
    dump_all()

    print("Done! Check above output to confirm final recalculated gains/losses, ledger entries, etc.")


if __name__ == "__main__":
    main()
