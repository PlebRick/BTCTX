# FILE: backend/tests/dumpAll.py

import requests
import json
import sys

BASE_URL = "http://localhost:8000"  # Adjust if your FastAPI server is on another port or domain.

def main():
    """
    Fetch and print all relevant BitcoinTX data:
      1. Transactions ( /api/transactions )
      2. Lots (  /api/debug/lots )       [dev-only router]
      3. Disposals ( /api/debug/disposals )  [dev-only router]
      4. Ledger Entries ( /api/debug/ledger-entries ) [dev-only router]
      5. Account Balances ( /api/calculations/accounts/balances )
      6. Gains & Losses ( /api/calculations/gains-and-losses )
      7. (Optional) Average Cost Basis ( /api/calculations/average-cost-basis )
    Prints each section as JSON in the terminal for easy inspection.
    """

    # A small helper to do GET
    def get_json(endpoint: str):
        url = f"{BASE_URL}{endpoint}"
        resp = requests.get(url)
        if not resp.ok:
            print(f"Failed GET {endpoint}: {resp.status_code} {resp.text}")
            return None
        return resp.json()

    print("----- 1) /api/transactions -----")
    tx_data = get_json("/api/transactions")
    print_json(tx_data)

    # The following debug endpoints presumably exist in your "routers.debug.py" or similar dev routers.
    # If you named them differently, just adjust the paths:
    print("\n----- 2) /api/debug/lots -----")
    lots_data = get_json("/api/debug/lots")
    print_json(lots_data)

    print("\n----- 3) /api/debug/disposals -----")
    disposals_data = get_json("/api/debug/disposals")
    print_json(disposals_data)

    print("\n----- 4) /api/debug/ledger-entries -----")
    ledger_data = get_json("/api/debug/ledger-entries")
    print_json(ledger_data)

    print("\n----- 5) /api/calculations/accounts/balances -----")
    balances_data = get_json("/api/calculations/accounts/balances")
    print_json(balances_data)

    print("\n----- 6) /api/calculations/gains-and-losses -----")
    gains_data = get_json("/api/calculations/gains-and-losses")
    print_json(gains_data)

    print("\n----- 7) /api/calculations/average-cost-basis -----")
    acb_data = get_json("/api/calculations/average-cost-basis")
    print_json(acb_data)

    print("\nAll data fetched and displayed.\n")


def print_json(data):
    """
    Helper function to pretty-print JSON. If 'data' is None, it means the endpoint failed.
    """
    if data is None:
        print("  (No data or request failed)")
        return
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
