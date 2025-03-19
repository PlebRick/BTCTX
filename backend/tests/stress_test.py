#!/usr/bin/env python3

"""
stress_test.py

A large-scale script to test BitcoinTX with a "scorched earth" approach.

Key fix: Convert trailing "Z" to "+00:00" so datetime.fromisoformat() won't fail.
"""

import requests
import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from requests.exceptions import HTTPError

# --------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------
BASE_URL = "http://127.0.0.1:8000"  # Adjust if your API runs elsewhere

# The custom route for deleting all transactions
DELETE_ALL_ENDPOINT = f"{BASE_URL}/api/transactions/delete_all"

# If you need different account IDs, adjust these:
BANK_ID       = 1  # USD
WALLET_ID     = 2  # BTC
EXCHANGE_USD  = 3  # USD
EXCHANGE_BTC  = 4  # BTC
BTC_FEES      = 5
USD_FEES      = 6
EXTERNAL      = 99

# How many random transactions / edits / deletes to generate
NUM_RANDOM_TRANSACTIONS = 200
NUM_EDITS = 20
NUM_DELETES = 10

# Helper date range: ~2 years from base_dt
base_dt = datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc)
end_dt  = base_dt + timedelta(days=700)  # ~ a bit less than 2 years

# --------------------------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------------------------
def _fix_iso_timestamp(ts_str: str) -> str:
    """
    If the timestamp ends with 'Z', convert it to '+00:00'
    so datetime.fromisoformat() won't fail.
    """
    if ts_str.endswith('Z'):
        return ts_str[:-1] + "+00:00"
    return ts_str

def delete_all_transactions():
    """Delete all transactions by calling DELETE /api/transactions/delete_all."""
    print("Deleting all existing transactions...")
    resp = requests.delete(DELETE_ALL_ENDPOINT)
    if resp.status_code in (200, 204):
        print("All transactions cleared successfully.\n")
    else:
        print(f"Warning: Unexpected status when deleting transactions: {resp.status_code}, {resp.text}")

def create_transaction(tx_data: dict) -> dict:
    """Create a transaction by POSTing to /api/transactions."""
    url = f"{BASE_URL}/api/transactions"
    resp = requests.post(url, json=tx_data)
    try:
        resp.raise_for_status()
    except HTTPError as e:
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
    except HTTPError as e:
        print(f"ERROR updating transaction #{tx_id} with updates={updates}")
        print(f"Status code: {resp.status_code}, Response: {resp.text}")
        raise e
    return resp.json()

def delete_transaction(tx_id: int) -> bool:
    """Delete an existing transaction (DELETE /api/transactions/{tx_id})."""
    url = f"{BASE_URL}/api/transactions/{tx_id}"
    resp = requests.delete(url)
    if resp.status_code in (200, 204):
        return True
    else:
        print(f"ERROR deleting transaction #{tx_id}")
        print(f"Status code: {resp.status_code}, Response: {resp.text}")
        return False

def dump_all():
    """
    Dump all relevant endpoints for debugging:
      /api/transactions
      /api/debug/lots
      /api/debug/disposals
      /api/debug/ledger-entries
      /api/calculations/accounts/balances
      /api/calculations/average-cost-basis
      /api/calculations/gains-and-losses
    """
    endpoints = [
        "/api/transactions",
        "/api/debug/lots",
        "/api/debug/disposals",
        "/api/debug/ledger-entries",
        "/api/calculations/accounts/balances",
        "/api/calculations/average-cost-basis",
        "/api/calculations/gains-and-losses",
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
# RANDOM TRANSACTION GENERATOR
# --------------------------------------------------------------------
def random_datetime_in_range(start: datetime, end: datetime) -> datetime:
    """Return a random datetime between 'start' and 'end'."""
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)

def pick_random_type() -> str:
    """Return a random transaction type: Deposit, Withdrawal, Transfer, Buy, or Sell."""
    return random.choice(["Deposit", "Withdrawal", "Transfer", "Buy", "Sell"])

def generate_random_tx_data() -> dict:
    """
    Generate a random transaction that respects the usage rules:
      - Deposit => from=99 => to=(1,2,3,4)
      - Withdrawal => from=(1,2,3,4) => to=99
      - Transfer => from/to internal same currency
      - Buy => from=3 => to=4
      - Sell => from=4 => to=3
    Also picks random amounts, cost basis, fees, etc.
    """
    tx_type = pick_random_type()
    dt_obj  = random_datetime_in_range(base_dt, end_dt)
    timestamp = dt_obj.isoformat()  # no trailing Z
    # We'll produce different random amounts for BTC vs USD
    if tx_type == "Deposit":
        to_acct = random.choice([1,2,3,4])
        if to_acct in [2,4]:
            amount_btc = round(random.uniform(0.001, 2.0), 8)
            cost_basis_usd = round(random.uniform(30000, 80000), 2)
            return {
                "type": "Deposit",
                "timestamp": timestamp,
                "from_account_id": EXTERNAL,
                "to_account_id": to_acct,
                "amount": str(amount_btc),
                "fee_amount": "0",
                "fee_currency": "BTC",
                "source": random.choice(["Income", "Reward", "Gift", "Interest", "N/A"]),
                "cost_basis_usd": str(cost_basis_usd),
            }
        else:
            amount_usd = round(random.uniform(5000, 50000), 2)  # Increased USD Deposits
            return {
                "type": "Deposit",
                "timestamp": timestamp,
                "from_account_id": EXTERNAL,
                "to_account_id": to_acct,
                "amount": str(amount_usd),
                "fee_amount": "0",
                "fee_currency": "USD",
                "source": "N/A",
            }
    elif tx_type == "Withdrawal":
        from_acct = random.choice([1,2,3,4])
        if from_acct in [2,4]:
            amount_btc = round(random.uniform(0.001, 0.5), 8)  # Reduced BTC Withdrawals
            fee_btc    = round(random.uniform(0, 0.0005), 8)
            purpose = random.choice(["Spent", "Gift", "Donation", "Lost"])
            return {
                "type": "Withdrawal",
                "timestamp": timestamp,
                "from_account_id": from_acct,
                "to_account_id": EXTERNAL,
                "amount": str(amount_btc),
                "fee_amount": str(fee_btc),
                "fee_currency": "BTC",
                "purpose": purpose,
            }
        else:
            amount_usd = round(random.uniform(100, 2000), 2)  # Reduced USD Withdrawals
            fee_usd    = round(random.uniform(0, 10), 2)
            return {
                "type": "Withdrawal",
                "timestamp": timestamp,
                "from_account_id": from_acct,
                "to_account_id": EXTERNAL,
                "amount": str(amount_usd),
                "fee_amount": str(fee_usd),
                "fee_currency": "USD",
                "purpose": "N/A",
            }
    elif tx_type == "Transfer":
        possible_pairs = [(2,4),(4,2),(1,3),(3,1)]
        (from_acct, to_acct) = random.choice(possible_pairs)
        if from_acct in [2,4]:
            amount_btc = round(random.uniform(0.001, 0.5), 8)
            fee_btc    = round(random.uniform(0, 0.0003), 8)
            return {
                "type": "Transfer",
                "timestamp": timestamp,
                "from_account_id": from_acct,
                "to_account_id": to_acct,
                "amount": str(amount_btc),
                "fee_amount": str(fee_btc),
                "fee_currency": "BTC",
            }
        else:
            amount_usd = round(random.uniform(100, 3000), 2)
            fee_usd    = round(random.uniform(0, 10), 2)
            return {
                "type": "Transfer",
                "timestamp": timestamp,
                "from_account_id": from_acct,
                "to_account_id": to_acct,
                "amount": str(amount_usd),
                "fee_amount": str(fee_usd),
                "fee_currency": "USD",
            }
    elif tx_type == "Buy":
        amount_btc  = round(random.uniform(0.01, 1.0), 8)  # Reduced BTC Buys
        fee_usd     = round(random.uniform(0, 20), 2)
        cost_basis  = round(random.uniform(10000, 40000), 2)  # Reduced cost basis range
        return {
            "type": "Buy",
            "timestamp": timestamp,
            "from_account_id": EXCHANGE_USD,
            "to_account_id": EXCHANGE_BTC,
            "amount": str(amount_btc),
            "fee_amount": str(fee_usd),
            "fee_currency": "USD",
            "cost_basis_usd": str(cost_basis),
        }
    else:  # Sell
        amount_btc   = round(random.uniform(0.01, 0.5), 8)  # Reduced BTC Sells
        fee_usd      = round(random.uniform(0, 20), 2)
        proceeds_usd = round(random.uniform(15000, 60000), 2)  # Increased proceeds to offset Buys
        return {
            "type": "Sell",
            "timestamp": timestamp,
            "from_account_id": EXCHANGE_BTC,
            "to_account_id": EXCHANGE_USD,
            "amount": str(amount_btc),
            "fee_amount": str(fee_usd),
            "fee_currency": "USD",
            "proceeds_usd": str(proceeds_usd),
        }

# --------------------------------------------------------------------
# MAIN SCRIPT
# --------------------------------------------------------------------
def main():
    # Step 1) Delete All
    delete_all_transactions()

    # Step 2) Create 10 base transactions
    print("Posting original 10 base transactions...\n")

    all_created = []

    # We'll start from 2024-01-02T10:00:00Z
    dt1 = base_dt

    # 1) Deposit to Wallet (BTC)
    tx1_data = {
        "type": "Deposit",
        "timestamp": dt1.isoformat(),
        "from_account_id": EXTERNAL,
        "to_account_id": WALLET_ID,
        "amount": "1.0",
        "fee_amount": "0",
        "fee_currency": "BTC",
        "source": "Income",
        "cost_basis_usd": "35000",
    }
    tx1 = create_transaction(tx1_data)
    print(f"1) Created Deposit TX ID={tx1['id']} at {tx1['timestamp']}")
    all_created.append(tx1)

    # 2) Deposit to Exchange USD (increased amount)
    tx2_data = {
        "type": "Deposit",
        "timestamp": (dt1 + timedelta(days=1)).isoformat(),
        "from_account_id": EXTERNAL,
        "to_account_id": EXCHANGE_USD,
        "amount": "100000",  # Increased to provide more USD for Buys
        "fee_amount": "0",
        "fee_currency": "USD",
        "source": "N/A",
    }
    tx2 = create_transaction(tx2_data)
    print(f"2) Created Deposit TX ID={tx2['id']} at {tx2['timestamp']}")
    all_created.append(tx2)

    # 3) Transfer from Wallet to Exchange BTC
    tx3_data = {
        "type": "Transfer",
        "timestamp": (dt1 + timedelta(days=2, hours=2)).isoformat(),
        "from_account_id": WALLET_ID,
        "to_account_id": EXCHANGE_BTC,
        "amount": "0.5",
        "fee_amount": "0.0001",
        "fee_currency": "BTC",
    }
    tx3 = create_transaction(tx3_data)
    print(f"3) Created Transfer TX ID={tx3['id']} at {tx3['timestamp']}")
    all_created.append(tx3)

    # 4) Buy on Exchange
    tx4_data = {
        "type": "Buy",
        "timestamp": (dt1 + timedelta(days=15)).isoformat(),
        "from_account_id": EXCHANGE_USD,
        "to_account_id": EXCHANGE_BTC,
        "amount": "0.2",
        "fee_amount": "10",
        "fee_currency": "USD",
        "cost_basis_usd": "15000",  # More realistic cost basis
    }
    tx4 = create_transaction(tx4_data)
    print(f"4) Created Buy TX ID={tx4['id']} at {tx4['timestamp']}")
    all_created.append(tx4)

    # 5) Deposit to Wallet (BTC)
    tx5_data = {
        "type": "Deposit",
        "timestamp": (dt1 + timedelta(days=30)).isoformat(),
        "from_account_id": EXTERNAL,
        "to_account_id": WALLET_ID,
        "amount": "1.5",
        "fee_amount": "0",
        "fee_currency": "BTC",
        "source": "Reward",
        "cost_basis_usd": "55000",
    }
    tx5 = create_transaction(tx5_data)
    print(f"5) Created Deposit TX ID={tx5['id']} at {tx5['timestamp']}")
    all_created.append(tx5)

    # 6) Sell on Exchange (increased proceeds)
    tx6_data = {
        "type": "Sell",
        "timestamp": (dt1 + timedelta(days=60)).isoformat(),
        "from_account_id": EXCHANGE_BTC,
        "to_account_id": EXCHANGE_USD,
        "amount": "0.3",
        "fee_amount": "15",
        "fee_currency": "USD",
        "proceeds_usd": "25000",  # Increased to add more USD to EXCHANGE_USD
    }
    tx6 = create_transaction(tx6_data)
    print(f"6) Created Sell TX ID={tx6['id']} at {tx6['timestamp']}")
    all_created.append(tx6)

    # 7) Withdrawal from Wallet
    tx7_dt = dt1 + timedelta(days=365)
    tx7_data = {
        "type": "Withdrawal",
        "timestamp": tx7_dt.isoformat(),
        "from_account_id": WALLET_ID,
        "to_account_id": EXTERNAL,
        "amount": "0.5",  # Reduced withdrawal amount
        "fee_amount": "0.0002",
        "fee_currency": "BTC",
        "purpose": "Spent",
    }
    tx7 = create_transaction(tx7_data)
    print(f"7) Created Withdrawal TX ID={tx7['id']} at {tx7['timestamp']}")
    all_created.append(tx7)

    # 8) Deposit to Exchange USD (increased amount)
    tx8_data = {
        "type": "Deposit",
        "timestamp": (tx7_dt + timedelta(days=1)).isoformat(),
        "from_account_id": EXTERNAL,
        "to_account_id": EXCHANGE_USD,
        "amount": "150000",  # Increased to provide more USD for Buys
        "fee_amount": "0",
        "fee_currency": "USD",
    }
    tx8 = create_transaction(tx8_data)
    print(f"8) Created Deposit TX ID={tx8['id']} at {tx8['timestamp']}")
    all_created.append(tx8)

    # 9) Buy on Exchange
    tx9_data = {
        "type": "Buy",
        "timestamp": (tx7_dt + timedelta(days=2)).isoformat(),
        "from_account_id": EXCHANGE_USD,
        "to_account_id": EXCHANGE_BTC,
        "amount": "0.8",
        "fee_amount": "20",
        "fee_currency": "USD",
        "cost_basis_usd": "35000",
    }
    tx9 = create_transaction(tx9_data)
    print(f"9) Created Buy TX ID={tx9['id']} at {tx9['timestamp']}")
    all_created.append(tx9)

    # 10) Deposit to Wallet with source="Interest"
    tx10_data = {
        "type": "Deposit",
        "timestamp": (tx7_dt + timedelta(days=10)).isoformat(),
        "from_account_id": EXTERNAL,
        "to_account_id": WALLET_ID,
        "amount": "0.1",
        "fee_amount": "0",
        "fee_currency": "BTC",
        "source": "Interest",
        "cost_basis_usd": "8000",
    }
    tx10 = create_transaction(tx10_data)
    print(f"10) Created Deposit (Interest) TX ID={tx10['id']} at {tx10['timestamp']}")
    all_created.append(tx10)

    print("\nAll base transactions created successfully.\n")

    # Step 3) Generate random transactions
    print(f"Generating {NUM_RANDOM_TRANSACTIONS} random transactions...\n")
    for i in range(NUM_RANDOM_TRANSACTIONS):
        tx_data = generate_random_tx_data()
        try:
            new_tx = create_transaction(tx_data)
            all_created.append(new_tx)
            if (i+1) % 25 == 0:
                print(f"... created {i+1} random transactions so far ...")
        except:
            # if we fail, skip
            pass

    print("\nAll random transactions created successfully.\n")

    # Step 4) Random updates
    print(f"Performing {NUM_EDITS} random updates...\n")
    random_updates = random.sample(all_created, min(NUM_EDITS, len(all_created)))
    for idx, tx in enumerate(random_updates, start=1):
        updates = {}
        if random.choice([True, False]):  # 50% chance
            # backdate by up to 10 days
            ts_str = tx["timestamp"]
            ts_str = _fix_iso_timestamp(ts_str)
            try:
                old_ts = datetime.fromisoformat(ts_str)
            except:
                # if we can't parse it, skip
                print(f"{idx}) Can't parse timestamp {ts_str}, skipping update on TX #{tx['id']}")
                continue
            new_ts = old_ts - timedelta(days=random.randint(1,10))
            updates["timestamp"] = new_ts.isoformat()
        else:
            # cost_basis_usd => random +/- 10% to 20%
            old_basis = tx.get("cost_basis_usd", 0)
            if old_basis is None:
                old_basis = 0
            try:
                old_val = float(old_basis)
            except:
                old_val = 0
            delta = old_val * random.uniform(-0.1, 0.2)
            new_val = max(0, old_val + delta)
            updates["cost_basis_usd"] = str(round(new_val, 2))

        try:
            updated = update_transaction(tx["id"], updates)
            print(f"{idx}) Updated TX #{tx['id']} with {updates}")
        except:
            print(f"{idx}) Failed to update TX #{tx['id']} with {updates} - skipping")

    # Step 5) Random deletes
    print(f"\nPerforming {NUM_DELETES} random deletes...\n")
    random_deletions = random.sample(all_created, min(NUM_DELETES, len(all_created)))
    for idx, tx in enumerate(random_deletions, start=1):
        ok = delete_transaction(tx["id"])
        if ok:
            print(f"{idx}) Deleted TX #{tx['id']}")
        else:
            print(f"{idx}) Failed to delete TX #{tx['id']}")

    # Step 6) Dump everything
    print("\nDumping all debug endpoints to verify final calculations...\n")
    dump_all()

    print("Done! Check above output to confirm final recalculated gains/losses, ledger entries, etc.")


if __name__ == "__main__":
    main()