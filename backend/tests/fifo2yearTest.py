# FILE: backend/tests/fifo2yearTest.py

import requests
from decimal import Decimal
import sys

BASE_URL = "http://localhost:8000"  # Adjust if your FastAPI server is at a different location.

def main():
    """
    Seed a simulated 2-year timeline of deposits, transfers, buys, sells, and withdrawals
    for testing FIFO and holding periods. All transactions are posted via the /api/transactions endpoint.
    """
    # 1) Clear existing transactions
    print("Deleting all existing transactions...")
    delete_all_url = f"{BASE_URL}/api/transactions/delete_all"
    resp = requests.delete(delete_all_url)
    if not resp.ok:
        print(f"Failed to delete all transactions: {resp.status_code} {resp.text}")
        sys.exit(1)

    print("All transactions cleared successfully.\n")

    # We'll define our chronological timeline, from Jan 2023 to Mar 2025
    # so that some transactions are older than 365 days by the final reference date.

    # 2) Create a list of transaction payloads
    # We define them in ascending date order. 
    # You can adjust amounts, fee_amount, sources, etc.
    tx_payloads = [
        # ------------------ 1) Deposits (2 long-term, 3 short-term) ------------------
        # Let's pick times so two are more than 365 days from 2025-03-15, 
        # making them "Jan 2023" for long-term, then the other 3 in mid/late 2024 for short-term.

        # Long-term deposit #1 => Wallet (BTC, source=Income)
        {
            "type": "Deposit",
            "timestamp": "2023-01-10T12:00:00Z",
            "from_account_id": 99,   # external
            "to_account_id": 2,     # Wallet
            "amount": "0.60000000",
            "fee_amount": "0.0",
            "fee_currency": "BTC",
            "source": "Income",     # or MyBTC, etc.
            "cost_basis_usd": "30000.00"
        },
        # Long-term deposit #2 => Bank (USD, source=N/A)
        {
            "type": "Deposit",
            "timestamp": "2023-01-11T12:00:00Z",
            "from_account_id": 99,
            "to_account_id": 1,    # Bank
            "amount": "20000.00",
            "fee_amount": "0.0",
            "fee_currency": "USD",
            "source": "N/A",
            "cost_basis_usd": "0.00"
        },
        # Short-term deposit #1 => Exchange BTC (BTC, source=Reward)
        {
            "type": "Deposit",
            "timestamp": "2024-08-01T12:00:00Z",
            "from_account_id": 99,
            "to_account_id": 4,    # Exchange BTC
            "amount": "0.30000000",
            "fee_amount": "0.0",
            "fee_currency": "BTC",
            "source": "Reward",
            "cost_basis_usd": "18000.00"
        },
        # Short-term deposit #2 => Exchange USD (USD, source=N/A)
        {
            "type": "Deposit",
            "timestamp": "2024-08-02T12:00:00Z",
            "from_account_id": 99,
            "to_account_id": 3,   # Exchange USD
            "amount": "15000.00",
            "fee_amount": "0.0",
            "fee_currency": "USD",
            "source": "N/A",
            "cost_basis_usd": "0.00"
        },
        # Short-term deposit #3 => Wallet (BTC, source=Gift)
        {
            "type": "Deposit",
            "timestamp": "2024-09-01T12:00:00Z",
            "from_account_id": 99,
            "to_account_id": 2,   # Wallet
            "amount": "0.40000000",
            "fee_amount": "0.0",
            "fee_currency": "BTC",
            "source": "Gift",
            "cost_basis_usd": "22000.00"
        },

        # ------------------ 2) Transfers among valid pairs ------------------
        # Bank -> Exchange USD
        {
            "type": "Transfer",
            "timestamp": "2024-10-01T12:00:00Z",
            "from_account_id": 1,  # Bank
            "to_account_id": 3,    # Exchange USD
            "amount": "5000.00",
            "fee_amount": "0.0",
            "fee_currency": "USD"
        },
        # Exchange USD -> Bank
        {
            "type": "Transfer",
            "timestamp": "2024-10-02T12:00:00Z",
            "from_account_id": 3,
            "to_account_id": 1,
            "amount": "2000.00",
            "fee_amount": "0.0",
            "fee_currency": "USD"
        },
        # Wallet -> Exchange BTC
        {
            "type": "Transfer",
            "timestamp": "2024-10-03T12:00:00Z",
            "from_account_id": 2,
            "to_account_id": 4,
            "amount": "0.20000000",
            "fee_amount": "0.00020000",
            "fee_currency": "BTC"
        },
        # Exchange BTC -> Wallet
        {
            "type": "Transfer",
            "timestamp": "2024-10-04T12:00:00Z",
            "from_account_id": 4,
            "to_account_id": 2,
            "amount": "0.10000000",
            "fee_amount": "0.00010000",
            "fee_currency": "BTC"
        },

        # ------------------ 3) Buys ------------------
        # Long-term Buy => We'll do date=2024-01-15, from Exchange USD to Exchange BTC
        # (We want it older than 365 days from a final 2025 date— or we can call it "long" if you want)
        {
            "type": "Buy",
            "timestamp": "2024-01-15T12:00:00Z",
            "from_account_id": 3,  # Exchange USD
            "to_account_id": 4,    # Exchange BTC
            "amount": "0.05000000",     # BTC purchased
            "fee_amount": "5.00",       # USD fee
            "fee_currency": "USD",
            "cost_basis_usd": "1500.00" # cost basis for the 0.05 BTC
        },
        # Short-term Buy => date=2025-02-15
        {
            "type": "Buy",
            "timestamp": "2025-02-15T12:00:00Z",
            "from_account_id": 3,  
            "to_account_id": 4,
            "amount": "0.02000000",
            "fee_amount": "2.00",
            "fee_currency": "USD",
            "cost_basis_usd": "600.00"
        },

        # ------------------ 4) Sells ------------------
        # Long-term Sell => We'll do date=2025-02-20 (just after the 2024-01-15 buy => ~1+ years)
        {
            "type": "Sell",
            "timestamp": "2025-02-20T12:00:00Z",
            "from_account_id": 4,  # Exchange BTC
            "to_account_id": 3,    # Exchange USD
            "amount": "0.05000000",   # selling that 0.05 BTC
            "fee_amount": "10.00",    # fee in USD
            "fee_currency": "USD",
            "cost_basis_usd": "1500.00",  # might be the same as the buy cost basis
            "proceeds_usd": "2100.00"
        },
        # Short-term Sell => 2025-03-01
        {
            "type": "Sell",
            "timestamp": "2025-03-01T12:00:00Z",
            "from_account_id": 4,
            "to_account_id": 3,
            "amount": "0.02000000",   
            "fee_amount": "2.00",
            "fee_currency": "USD",
            "cost_basis_usd": "600.00",
            "proceeds_usd": "900.00"
        },

        # ------------------ 5) Withdrawals (Wallet or Exchange, with various purposes) ------------------
        # We'll do a few, mixing short/long.
        # a) long-term from wallet => date=2025-02-25
        {
            "type": "Withdrawal",
            "timestamp": "2025-02-25T12:00:00Z",
            "from_account_id": 2,  # wallet
            "to_account_id": 99,
            "amount": "0.10000000",
            "fee_amount": "0.00010000",
            "fee_currency": "BTC",
            "purpose": "Spent",
            "cost_basis_usd": "2000.00",   # example
            "proceeds_usd": "3500.00"
        },
        # b) short-term from Exchange BTC => 2025-03-05 => Gift
        {
            "type": "Withdrawal",
            "timestamp": "2025-03-05T12:00:00Z",
            "from_account_id": 4,
            "to_account_id": 99,
            "amount": "0.05000000",
            "fee_amount": "0.00025000",
            "fee_currency": "BTC",
            "purpose": "Gift",
            "cost_basis_usd": "2200.00",
            "proceeds_usd": "0.00"  # 'Gift' => aggregator sets realized_gain=0
        },
        # c) short-term from Wallet => Donation
        {
            "type": "Withdrawal",
            "timestamp": "2025-03-06T12:00:00Z",
            "from_account_id": 2,
            "to_account_id": 99,
            "amount": "0.05000000",
            "fee_amount": "0.00010000",
            "fee_currency": "BTC",
            "purpose": "Donation",
            "cost_basis_usd": "1000.00",
            "proceeds_usd": "0.00"  # aggregator => realized_gain=0
        },
        # d) short-term from Exchange => Lost
        {
            "type": "Withdrawal",
            "timestamp": "2025-03-07T12:00:00Z",
            "from_account_id": 4,
            "to_account_id": 99,
            "amount": "0.01000000",
            "fee_amount": "0.00005000",
            "fee_currency": "BTC",
            "purpose": "Lost",
            "cost_basis_usd": "300.00",
            "proceeds_usd": "0.00" 
        },

        # e) Withdraw some USD from Bank => short-term
        {
            "type": "Withdrawal",
            "timestamp": "2025-03-08T12:00:00Z",
            "from_account_id": 1,
            "to_account_id": 99,
            "amount": "1000.00",
            "fee_amount": "0.0",
            "fee_currency": "USD",
            "purpose": "Spent",
            "cost_basis_usd": "0.00",
            "proceeds_usd": "1000.00"
        },
        # f) Withdraw some USD from Exchange USD => short-term
        {
            "type": "Withdrawal",
            "timestamp": "2025-03-09T12:00:00Z",
            "from_account_id": 3,
            "to_account_id": 99,
            "amount": "500.00",
            "fee_amount": "0.0",
            "fee_currency": "USD",
            "purpose": "Spent",
            "cost_basis_usd": "0.00",
            "proceeds_usd": "500.00"
        },

    ]

    # 3) POST each transaction in ascending order
    print("Posting each transaction in chronological order...\n")
    for i, payload in enumerate(tx_payloads, start=1):
        url = f"{BASE_URL}/api/transactions"
        resp = requests.post(url, json=payload)
        if resp.ok:
            tx_resp = resp.json()
            print(f"{i}) Created {tx_resp['type']} TX at {tx_resp['timestamp']} - ID={tx_resp['id']}")
        else:
            print(f"{i}) Failed to create transaction: {resp.status_code} {resp.text}")
            sys.exit(1)

    # 4) Retrieve final Gains/Losses
    print("\nFinal Gains & Losses from aggregator:\n")
    gains_url = f"{BASE_URL}/api/calculations/gains-and-losses"
    gains_resp = requests.get(gains_url)
    if gains_resp.ok:
        print(gains_resp.json())
    else:
        print(f"Failed to retrieve Gains: {gains_resp.status_code} {gains_resp.text}")

    # 5) Retrieve final account balances
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
