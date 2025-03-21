#!/usr/bin/env python3

"""
realistic_test.py

A realistic test scenario for BitcoinTX from Jan 1, 2022, to Mar 20, 2025.
Simulates a user with various transaction types across all accounts.
Place this file in your BitcoinTX project's `tests/` directory.
"""

import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List
import random

# --------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------
BASE_URL = "http://127.0.0.1:8000"  # Adjust for your FastAPI server
DELETE_ALL_ENDPOINT = f"{BASE_URL}/api/transactions/delete_all"

# Account IDs (consistent with your setup)
BANK_ID       = 1  # USD
WALLET_ID     = 2  # BTC
EXCHANGE_USD  = 3  # USD
EXCHANGE_BTC  = 4  # BTC
BTC_FEES      = 5  # BTC
USD_FEES      = 6  # USD
EXTERNAL      = 99 # External entity

# Date range
START_DATE = datetime(2022, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
END_DATE   = datetime(2025, 3, 20, 18, 29, 0, tzinfo=timezone.utc)  # Today, 6:29 PM PDT

# Historical BTC prices (key dates)
BTC_PRICES = {
    "2022-01-01": 47459,
    "2022-05-11": 29000,
    "2022-06-13": 23000,
    "2022-12-31": 16530,
    "2023-12-31": 42258,
    "2024-03-14": 73805,
    "2024-12-05": 100000,
    "2025-01-20": 109350,
    "2025-03-20": 86815,
}

# --------------------------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------------------------
def get_btc_price(date: datetime) -> float:
    """Interpolate BTC price for a given date based on historical data."""
    dates = sorted([datetime.strptime(k, "%Y-%m-%d").replace(tzinfo=timezone.utc) for k in BTC_PRICES.keys()])
    prices = [BTC_PRICES[k] for k in sorted(BTC_PRICES.keys())]
    
    if date <= dates[0]:
        return prices[0]
    if date >= dates[-1]:
        return prices[-1]
    
    for i in range(len(dates) - 1):
        if dates[i] <= date < dates[i + 1]:
            days_between = (dates[i + 1] - dates[i]).days
            days_from_start = (date - dates[i]).days
            price_diff = prices[i + 1] - prices[i]
            return prices[i] + (price_diff * days_from_start / days_between)
    return prices[-1]  # Fallback

def delete_all_transactions():
    """Clear all transactions via API."""
    resp = requests.delete(DELETE_ALL_ENDPOINT)
    if resp.status_code in (200, 204):
        print("All transactions cleared.")
    else:
        print(f"Failed to clear transactions: {resp.status_code}, {resp.text}")

def create_transaction(tx_data: Dict) -> Dict:
    """Create a transaction via POST /api/transactions."""
    url = f"{BASE_URL}/api/transactions"
    resp = requests.post(url, json=tx_data)
    resp.raise_for_status()
    return resp.json()

# --------------------------------------------------------------------
# TRANSACTION GENERATORS
# --------------------------------------------------------------------
def generate_initial_deposits() -> List[Dict]:
    """Initial $10,000 USD deposits to Bank and Exchange."""
    txs = [
        {
            "type": "Deposit",
            "timestamp": START_DATE.isoformat(),
            "from_account_id": EXTERNAL,
            "to_account_id": BANK_ID,
            "amount": "10000",
            "fee_amount": "0",
            "fee_currency": "USD",
            "source": "N/A",
        },
        {
            "type": "Deposit",
            "timestamp": START_DATE.isoformat(),
            "from_account_id": EXTERNAL,
            "to_account_id": EXCHANGE_USD,
            "amount": "10000",
            "fee_amount": "0",
            "fee_currency": "USD",
            "source": "N/A",
        },
    ]
    return txs

def generate_dca_transactions() -> List[Dict]:
    """$10 USD daily BTC DCA from Exchange USD to BTC."""
    txs = []
    current_date = START_DATE
    while current_date <= END_DATE:
        price = get_btc_price(current_date)
        btc_amount = 10 / price
        fee_usd = round(10 * 0.002, 2)  # 0.2% fee
        txs.append({
            "type": "Buy",
            "timestamp": current_date.isoformat(),
            "from_account_id": EXCHANGE_USD,
            "to_account_id": EXCHANGE_BTC,
            "amount": str(round(btc_amount, 8)),
            "fee_amount": str(fee_usd),
            "fee_currency": "USD",
            "cost_basis_usd": "10",
        })
        current_date += timedelta(days=1)
    return txs

def generate_monthly_income() -> List[Dict]:
    """$1,000 USD worth of BTC monthly income to Wallet."""
    txs = []
    current_date = START_DATE.replace(day=1)
    while current_date <= END_DATE:
        price = get_btc_price(current_date)
        btc_amount = 1000 / price
        txs.append({
            "type": "Deposit",
            "timestamp": current_date.isoformat(),
            "from_account_id": EXTERNAL,
            "to_account_id": WALLET_ID,
            "amount": str(round(btc_amount, 8)),
            "fee_amount": "0",
            "fee_currency": "BTC",
            "source": "Income",
            "cost_basis_usd": "1000",
        })
        current_date += timedelta(days=31)
        current_date = current_date.replace(day=1)
    return txs

def generate_monthly_interest() -> List[Dict]:
    """$100 USD worth of BTC monthly interest to Wallet."""
    txs = []
    current_date = START_DATE.replace(day=15)
    while current_date <= END_DATE:
        price = get_btc_price(current_date)
        btc_amount = 100 / price
        txs.append({
            "type": "Deposit",
            "timestamp": current_date.isoformat(),
            "from_account_id": EXTERNAL,
            "to_account_id": WALLET_ID,
            "amount": str(round(btc_amount, 8)),
            "fee_amount": "0",
            "fee_currency": "BTC",
            "source": "Interest",
            "cost_basis_usd": "100",
        })
        current_date += timedelta(days=31)
        current_date = current_date.replace(day=15)
    return txs

def generate_monthly_rewards() -> List[Dict]:
    """$25 USD worth of BTC monthly rewards to Wallet."""
    txs = []
    current_date = START_DATE.replace(day=20)
    while current_date <= END_DATE:
        price = get_btc_price(current_date)
        btc_amount = 25 / price
        txs.append({
            "type": "Deposit",
            "timestamp": current_date.isoformat(),
            "from_account_id": EXTERNAL,
            "to_account_id": WALLET_ID,
            "amount": str(round(btc_amount, 8)),
            "fee_amount": "0",
            "fee_currency": "BTC",
            "source": "Reward",
            "cost_basis_usd": "25",
        })
        current_date += timedelta(days=31)
        current_date = current_date.replace(day=20)
    return txs

def generate_occasional_withdrawals() -> List[Dict]:
    """Occasional BTC withdrawals (50-200 USD) from Wallet."""
    txs = []
    current_date = START_DATE + timedelta(days=90)
    while current_date <= END_DATE:
        price = get_btc_price(current_date)
        usd_amount = random.uniform(50, 200)
        btc_amount = usd_amount / price
        fee_btc = round(btc_amount * 0.001, 8)  # 0.1% fee
        txs.append({
            "type": "Withdrawal",
            "timestamp": current_date.isoformat(),
            "from_account_id": WALLET_ID,
            "to_account_id": EXTERNAL,
            "amount": str(round(btc_amount, 8)),
            "fee_amount": str(fee_btc),
            "fee_currency": "BTC",
            "purpose": "Spent",
        })
        current_date += timedelta(days=random.randint(45, 90))
    return txs

def generate_annual_sells() -> List[Dict]:
    """Sell 25% of BTC at yearly highs."""
    txs = []
    sell_dates = [
        datetime(2022, 1, 15, tzinfo=timezone.utc),  # Early 2022 high
        datetime(2023, 12, 31, tzinfo=timezone.utc), # End of 2023
        datetime(2024, 3, 14, tzinfo=timezone.utc),  # 2024 peak
        datetime(2025, 1, 20, tzinfo=timezone.utc),  # 2025 peak
    ]
    accumulated_btc = 0.01  # Starting point after initial transfers
    for date in sell_dates:
        if date > END_DATE:
            break
        price = get_btc_price(date)
        sell_amount = accumulated_btc * 0.25
        fee_usd = round(sell_amount * price * 0.002, 2)  # 0.2% fee
        proceeds = round(sell_amount * price, 2)
        txs.extend([
            {
                "type": "Transfer",
                "timestamp": (date - timedelta(hours=1)).isoformat(),
                "from_account_id": WALLET_ID,
                "to_account_id": EXCHANGE_BTC,
                "amount": str(round(sell_amount, 8)),
                "fee_amount": "0.0001",
                "fee_currency": "BTC",
            },
            {
                "type": "Sell",
                "timestamp": date.isoformat(),
                "from_account_id": EXCHANGE_BTC,
                "to_account_id": EXCHANGE_USD,
                "amount": str(round(sell_amount, 8)),
                "fee_amount": str(fee_usd),
                "fee_currency": "USD",
                "proceeds_usd": str(proceeds),
            }
        ])
        accumulated_btc -= sell_amount  # Update after sell
        accumulated_btc += 0.05  # Approximate monthly accumulation
    return txs

def generate_low_buys() -> List[Dict]:
    """Buy $1,000 USD worth of BTC at lows."""
    txs = [
        {
            "type": "Buy",
            "timestamp": datetime(2022, 6, 13, tzinfo=timezone.utc).isoformat(),
            "from_account_id": EXCHANGE_USD,
            "to_account_id": EXCHANGE_BTC,
            "amount": str(round(1000 / 23000, 8)),
            "fee_amount": "2",
            "fee_currency": "USD",
            "cost_basis_usd": "1000",
        },
        {
            "type": "Buy",
            "timestamp": datetime(2022, 12, 31, tzinfo=timezone.utc).isoformat(),
            "from_account_id": EXCHANGE_USD,
            "to_account_id": EXCHANGE_BTC,
            "amount": str(round(1000 / 16530, 8)),
            "fee_amount": "2",
            "fee_currency": "USD",
            "cost_basis_usd": "1000",
        },
    ]
    return txs

def generate_transfers() -> List[Dict]:
    """Transfer BTC to Wallet when >= 0.01 BTC accumulates on Exchange."""
    txs = []
    current_date = START_DATE
    accumulated_btc = 0
    while current_date <= END_DATE:
        price = get_btc_price(current_date)
        daily_dca_btc = 10 / price
        accumulated_btc += daily_dca_btc
        if accumulated_btc >= 0.01:
            txs.append({
                "type": "Transfer",
                "timestamp": current_date.isoformat(),
                "from_account_id": EXCHANGE_BTC,
                "to_account_id": WALLET_ID,
                "amount": str(round(accumulated_btc, 8)),
                "fee_amount": "0.0001",
                "fee_currency": "BTC",
            })
            accumulated_btc = 0
        current_date += timedelta(days=1)
    return txs

def generate_annual_gifts_donations() -> List[Dict]:
    """Annual BTC withdrawals as Gift and Donation."""
    txs = []
    for year in [2022, 2023, 2024, 2025]:
        date = datetime(year, 12, 25, tzinfo=timezone.utc)
        if date > END_DATE:
            break
        price = get_btc_price(date)
        gift_amount = 100 / price
        donation_amount = 150 / price
        txs.extend([
            {
                "type": "Withdrawal",
                "timestamp": date.isoformat(),
                "from_account_id": WALLET_ID,
                "to_account_id": EXTERNAL,
                "amount": str(round(gift_amount, 8)),
                "fee_amount": "0.0001",
                "fee_currency": "BTC",
                "purpose": "Gift",
            },
            {
                "type": "Withdrawal",
                "timestamp": (date + timedelta(days=1)).isoformat(),
                "from_account_id": WALLET_ID,
                "to_account_id": EXTERNAL,
                "amount": str(round(donation_amount, 8)),
                "fee_amount": "0.0001",
                "fee_currency": "BTC",
                "purpose": "Donation",
            }
        ])
    return txs

# --------------------------------------------------------------------
# MAIN SCRIPT
# --------------------------------------------------------------------
def main():
    delete_all_transactions()

    # Generate all transactions
    all_txs = (
        generate_initial_deposits() +
        generate_dca_transactions() +
        generate_monthly_income() +
        generate_monthly_interest() +
        generate_monthly_rewards() +
        generate_occasional_withdrawals() +
        generate_annual_sells() +
        generate_low_buys() +
        generate_transfers() +
        generate_annual_gifts_donations()
    )

    # Sort by timestamp
    all_txs.sort(key=lambda x: datetime.fromisoformat(x["timestamp"]))

    # Create transactions via API
    print(f"Creating {len(all_txs)} transactions...")
    for i, tx in enumerate(all_txs, 1):
        try:
            created = create_transaction(tx)
            print(f"{i}) Created TX ID={created['id']} - {tx['type']} at {tx['timestamp']}")
        except Exception as e:
            print(f"Failed to create TX {i}: {tx}, Error: {e}")
        if i % 100 == 0:
            print(f"... processed {i} transactions ...")

    print("Test scenario completed. Verify via API endpoints like /api/calculations/gains-and-losses.")

if __name__ == "__main__":
    main()