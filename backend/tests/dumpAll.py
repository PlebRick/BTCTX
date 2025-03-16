# FILE: backend/tests/dumpAll.py

import requests
import json
import sys

BASE_URL = "http://localhost:8000"  # Adjust if your FastAPI server is on another port or domain.

def main():
    """
    Fetch and print all relevant BitcoinTX data:
      1. Transactions                ( /api/transactions )
      2. Lots                        ( /api/debug/lots )
      3. Disposals                   ( /api/debug/disposals )
      4. Ledger Entries              ( /api/debug/ledger-entries )
      5. Account Balances            ( /api/calculations/accounts/balances )
      6. Gains & Losses              ( /api/calculations/gains-and-losses )
      7. Average Cost Basis          ( /api/calculations/average-cost-basis )

    Prints each section in pretty-printed JSON for easy inspection.
    Matches the style of your new FIFO test script.
    """

    def get_json(endpoint: str):
        """
        Helper to GET <BASE_URL + endpoint> and return JSON data or None on failure.
        """
        url = f"{BASE_URL}{endpoint}"
        resp = requests.get(url)
        if not resp.ok:
            print(f"Failed GET {endpoint}: {resp.status_code} {resp.text}")
            return None
        return resp.json()

    def print_json(data, label: str):
        """
        Helper to pretty-print JSON. If 'data' is None, indicates failure.
        """
        print(f"\n----- {label} -----")
        if data is None:
            print("  (No data or request failed)")
            return
        print(json.dumps(data, indent=2))

    # 1) Transactions
    tx_data = get_json("/api/transactions")
    print_json(tx_data, "1) /api/transactions")

    # 2) Lots (debug)
    lots_data = get_json("/api/debug/lots")
    print_json(lots_data, "2) /api/debug/lots")

    # 3) Disposals (debug)
    disposals_data = get_json("/api/debug/disposals")
    print_json(disposals_data, "3) /api/debug/disposals")

    # 4) Ledger Entries (debug)
    ledger_data = get_json("/api/debug/ledger-entries")
    print_json(ledger_data, "4) /api/debug/ledger-entries")

    # 5) Account Balances
    balances_data = get_json("/api/calculations/accounts/balances")
    print_json(balances_data, "5) /api/calculations/accounts/balances")

    # 6) Gains & Losses
    gains_data = get_json("/api/calculations/gains-and-losses")
    print_json(gains_data, "6) /api/calculations/gains-and-losses")

    # 7) Average Cost Basis
    acb_data = get_json("/api/calculations/average-cost-basis")
    print_json(acb_data, "7) /api/calculations/average-cost-basis")

    print("\nAll data fetched and displayed.\n")

if __name__ == "__main__":
    main()
