# reports_api_test.py
"""
Basic script to test all the /reports endpoints.

Usage:
    python reports_api_test.py
"""

import requests

# Adjust this to point to your running FastAPI server
API_BASE_URL = "http://127.0.0.1:8000"  # or wherever your app runs

# A list of tuples: (endpoint, params, expected_content_type, is_pdf)
# You can add more lines for your new endpoints.
ENDPOINTS = [
    ("/reports/comprehensive_tax", {"year": 2024}, "application/pdf", True),
    ("/reports/form_8949",        {"year": 2024}, "application/pdf", True),
    ("/reports/schedule_d",       {"year": 2024}, "application/pdf", True),
    ("/reports/turbotax_export",  {"year": 2024}, "text/csv",        False),
    ("/reports/turbotax_cddvd",   {"year": 2024}, "text/plain",      False),
    ("/reports/taxact_export",    {"year": 2024}, "text/csv",        False),
    ("/reports/capital_gains",    {"year": 2024}, "text/csv",        False),
    ("/reports/income",           {"year": 2024}, "text/csv",        False),
    ("/reports/other_gains",      {"year": 2024}, None,              False),
    ("/reports/gifts_donations_lost", {"year": 2024}, "text/csv",    False),
    ("/reports/expenses",         {"year": 2024}, "text/csv",        False),
    ("/reports/beginning_year_holdings", {"year": 2024}, None,       False),
    ("/reports/end_year_holdings", {"year": 2024}, "text/csv",       False),
    ("/reports/highest_balance",  {"year": 2024}, None,              False),
    ("/reports/buy_sell_report",  {"year": 2024}, None,              False),
    ("/reports/ledger_balance",   {"year": 2024}, None,              False),
    ("/reports/balances_per_wallet", {"year": 2024}, None,           False),
    ("/reports/transaction_history", {"year": 2024}, "text/csv",     False),
]

def main():
    for route, params, expected_mime, is_pdf in ENDPOINTS:
        url = f"{API_BASE_URL}{route}"
        print(f"Testing endpoint: {url} with params={params}")
        try:
            response = requests.get(url, params=params, timeout=10)
        except requests.RequestException as e:
            print(f"  [ERROR] Could not connect: {e}")
            continue

        if response.status_code == 200:
            print("  [OK] 200 status")

            content_type = response.headers.get("Content-Type", "")
            if expected_mime is not None:
                # Check if the content type starts with the expected_mime
                if not content_type.startswith(expected_mime):
                    print(f"  [WARN] Unexpected Content-Type: {content_type}")
                else:
                    print(f"  [OK] Content-Type: {content_type}")
            else:
                print(f"  [INFO] No specific MIME check. Server returned: {content_type}")

            # If PDF, we might check first few bytes for "%PDF"
            if is_pdf:
                first_bytes = response.content[:5]
                if b"%PDF" in first_bytes:
                    print("  [OK] Looks like a PDF content (found %PDF)")
                else:
                    print(f"  [WARN] PDF not detected in first bytes: {first_bytes}")
            else:
                # If CSV or plain text, maybe just check length
                length = len(response.content)
                print(f"  [INFO] Content length: {length} bytes")
        else:
            print(f"  [ERROR] status {response.status_code}, body={response.text[:200]}")

    print("\nAll endpoints tested.")

if __name__ == "__main__":
    main()
