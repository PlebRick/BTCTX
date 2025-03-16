# FILE: backend/tests/fifo2yearTest.py

import requests
import sys
from dateutil import parser

BASE_URL = "http://localhost:8000"  # Adjust if your FastAPI server is at a different location.

def filter_payload(tx):
    """
    Remove server-generated fields from a transaction payload.
    So we only send what the POST /transactions endpoint expects.
    """
    exclude_keys = [
        "id", "is_locked", "created_at", "updated_at", 
        "realized_gain_usd", "holding_period"
    ]
    return {k: v for k, v in tx.items() if k not in exclude_keys}

def main():
    """
    Seed a new set of chronological transactions (covering >2 yrs),
    ensuring both short-term and long-term gains. This is our final test
    that uses your custom transaction set with deposit, transfer, buy, sell,
    and withdrawal scenarios in chronological order.
    """

    # 1) Clear existing transactions
    print("Deleting all existing transactions...")
    delete_all_url = f"{BASE_URL}/api/transactions/delete_all"
    resp = requests.delete(delete_all_url)
    if not resp.ok:
        print(f"Failed to delete all transactions: {resp.status_code} {resp.text}")
        sys.exit(1)
    print("All transactions cleared successfully.\n")

    # 2) Define the new transaction list (currently includes
    #    items in possibly random order, we will sort by timestamp).
    tx_payloads = [
        {
            "type": "Deposit",
            "timestamp": "2023-01-02T02:35:00Z",
            "from_account_id": 99,
            "to_account_id": 2,
            "amount": "1.00000000",
            "fee_amount": "0E-8",
            "fee_currency": "BTC",
            "source": "Income",
            "purpose": None,
            "cost_basis_usd": "16000.00",
            "proceeds_usd": None
        },
        {
            "type": "Transfer",
            "timestamp": "2025-01-02T02:36:00Z",
            "from_account_id": 2,
            "to_account_id": 4,
            "amount": "0.99900000",
            "fee_amount": "0.00010000",
            "fee_currency": "BTC",
            "source": None,
            "purpose": None,
            "cost_basis_usd": "0.00",
            "proceeds_usd": None
        },
        {
            "type": "Deposit",
            "timestamp": "2025-01-02T02:38:00Z",
            "from_account_id": 99,
            "to_account_id": 1,
            "amount": "10000.00000000",
            "fee_amount": "0E-8",
            "fee_currency": "USD",
            "source": "N/A",
            "purpose": None,
            "cost_basis_usd": "0.00",
            "proceeds_usd": None
        },
        {
            "type": "Deposit",
            "timestamp": "2025-01-02T02:39:00Z",
            "from_account_id": 99,
            "to_account_id": 3,
            "amount": "10000.00000000",
            "fee_amount": "0E-8",
            "fee_currency": "USD",
            "source": "N/A",
            "purpose": None,
            "cost_basis_usd": "0.00",
            "proceeds_usd": None
        },
        {
            "type": "Deposit",
            "timestamp": "2025-01-02T02:40:00Z",
            "from_account_id": 99,
            "to_account_id": 3,
            "amount": "10000.00000000",
            "fee_amount": "0E-8",
            "fee_currency": "USD",
            "source": "N/A",
            "purpose": None,
            "cost_basis_usd": "0.00",
            "proceeds_usd": None
        },
        {
            "type": "Buy",
            "timestamp": "2025-01-03T02:40:00Z",
            "from_account_id": 3,
            "to_account_id": 4,
            "amount": "1.00000000",
            "fee_amount": "1000.00000000",
            "fee_currency": "USD",
            "source": None,
            "purpose": None,
            "cost_basis_usd": "100000.00",
            "proceeds_usd": None
        },
        {
            "type": "Deposit",
            "timestamp": "2025-01-17T02:46:00Z",
            "from_account_id": 99,
            "to_account_id": 4,
            "amount": "0.00100000",
            "fee_amount": "0E-8",
            "fee_currency": "BTC",
            "source": "Interest",
            "purpose": None,
            "cost_basis_usd": "100.00",
            "proceeds_usd": None
        },
        {
            "type": "Transfer",
            "timestamp": "2025-02-04T02:44:00Z",
            "from_account_id": 4,
            "to_account_id": 2,
            "amount": "0.10000000",
            "fee_amount": "0E-8",
            "fee_currency": "BTC",
            "source": None,
            "purpose": None,
            "cost_basis_usd": "0.00",
            "proceeds_usd": None
        },
        {
            "type": "Deposit",
            "timestamp": "2025-03-01T02:47:00Z",
            "from_account_id": 99,
            "to_account_id": 4,
            "amount": "0.00100000",
            "fee_amount": "0E-8",
            "fee_currency": "BTC",
            "source": "Gift",
            "purpose": None,
            "cost_basis_usd": "100.00",
            "proceeds_usd": None
        },
        {
            "type": "Transfer",
            "timestamp": "2025-03-02T02:44:00Z",
            "from_account_id": 2,
            "to_account_id": 4,
            "amount": "0.10000000",
            "fee_amount": "0.00004410",
            "fee_currency": "BTC",
            "source": None,
            "purpose": None,
            "cost_basis_usd": "0.00",
            "proceeds_usd": None
        },
        {
            "type": "Deposit",
            "timestamp": "2025-03-02T02:48:00Z",
            "from_account_id": 99,
            "to_account_id": 4,
            "amount": "0.10000000",
            "fee_amount": "0E-8",
            "fee_currency": "BTC",
            "source": "Reward",
            "purpose": None,
            "cost_basis_usd": "82.00",
            "proceeds_usd": None
        },
        {
            "type": "Sell",
            "timestamp": "2025-03-17T01:54:00Z",
            "from_account_id": 4,
            "to_account_id": 3,
            "amount": "1.00000000",
            "fee_amount": "830.34000000",
            "fee_currency": "USD",
            "source": None,
            "purpose": None,
            "cost_basis_usd": "16012.24",
            "proceeds_usd": "82203.67"
        },
        {
            "type": "Withdrawal",
            "timestamp": "2025-03-17T01:57:00Z",
            "from_account_id": 4,
            "to_account_id": 99,
            "amount": "0.50000000",
            "fee_amount": "0.00010000",
            "fee_currency": "BTC",
            "purpose": "Spent",
            "cost_basis_usd": "50500.00",
            "proceeds_usd": "41538.69"
        },
        {
            "type": "Sell",
            "timestamp": "2025-03-17T01:58:00Z",
            "from_account_id": 4,
            "to_account_id": 3,
            "amount": "0.10000000",
            "fee_amount": "2.00000000",
            "fee_currency": "USD",
            "source": None,
            "purpose": None,
            "cost_basis_usd": "10100.00",
            "proceeds_usd": "10998.00"
        },
        {
            "type": "Withdrawal",
            "timestamp": "2025-03-17T02:00:00Z",
            "from_account_id": 2,
            "to_account_id": 99,
            "amount": "0.00009999",
            "fee_amount": "0E-8",
            "fee_currency": "BTC",
            "purpose": "Spent",
            "cost_basis_usd": "10.10",
            "proceeds_usd": "10.00"
        },
        {
            "type": "Withdrawal",
            "timestamp": "2025-03-17T02:02:00Z",
            "from_account_id": 2,
            "to_account_id": 99,
            "amount": "0.00090001",
            "fee_amount": "0E-8",
            "fee_currency": "BTC",
            "purpose": "Spent",
            "cost_basis_usd": "90.90",
            "proceeds_usd": "74.81"
        },
        {
            "type": "Withdrawal",
            "timestamp": "2025-03-17T02:04:00Z",
            "from_account_id": 4,
            "to_account_id": 99,
            "amount": "0.01000000",
            "fee_amount": "0.00010000",
            "fee_currency": "BTC",
            "purpose": "Gift",
            "cost_basis_usd": "1010.00",
            "proceeds_usd": "0.00"
        },
        {
            "type": "Withdrawal",
            "timestamp": "2025-03-17T02:04:00Z",
            "from_account_id": 4,
            "to_account_id": 99,
            "amount": "0.01000000",
            "fee_amount": "0.00010000",
            "fee_currency": "BTC",
            "purpose": "Donation",
            "cost_basis_usd": "1010.00",
            "proceeds_usd": "0.00"
        },
        {
            "type": "Withdrawal",
            "timestamp": "2025-03-17T02:05:00Z",
            "from_account_id": 4,
            "to_account_id": 99,
            "amount": "0.01000000",
            "fee_amount": "0E-8",
            "fee_currency": "BTC",
            "purpose": "Lost",
            "cost_basis_usd": "1010.00",
            "proceeds_usd": "0.00"
        },
    ]

    # 3) Sort by timestamp ascending
    sorted_txs = sorted(tx_payloads, key=lambda tx: parser.isoparse(tx["timestamp"]))

    # 4) POST them in order
    print("Posting each transaction in chronological order...\n")
    for i, raw_tx in enumerate(sorted_txs, start=1):
        # Filter out server-generated fields
        payload = filter_payload(raw_tx)

        url = f"{BASE_URL}/api/transactions"
        resp = requests.post(url, json=payload)
        if resp.ok:
            tx_resp = resp.json()
            print(f"{i}) Created {tx_resp['type']} TX at {tx_resp['timestamp']} - ID={tx_resp['id']}")
        else:
            print(f"{i}) Failed to create transaction: {resp.status_code} {resp.text}")
            sys.exit(1)

    # 5) Retrieve final Gains/Losses
    print("\nFinal Gains & Losses from aggregator:\n")
    gains_url = f"{BASE_URL}/api/calculations/gains-and-losses"
    gains_resp = requests.get(gains_url)
    if gains_resp.ok:
        print(gains_resp.json())
    else:
        print(f"Failed to retrieve Gains: {gains_resp.status_code} {gains_resp.text}")

    # 6) Retrieve final account balances
    print("\nFinal Account Balances:\n")
    bal_url = f"{BASE_URL}/api/calculations/accounts/balances"
    bal_resp = requests.get(bal_url)
    if bal_resp.ok:
        for acct in bal_resp.json():
            print(acct)
    else:
        print(f"Failed to retrieve balances: {bal_resp.status_code} {bal_resp.text}")

    print("\nAll done! You can now see the seeded transactions and aggregator results in your front end.")

if __name__ == "__main__":
    main()
