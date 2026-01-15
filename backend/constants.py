"""
Account ID constants matching database seed values from database.py.
These are the fixed accounts created at startup.
"""

# Core accounts (seeded in database.py)
ACCOUNT_BANK = 1
ACCOUNT_WALLET = 2
ACCOUNT_EXCHANGE_USD = 3
ACCOUNT_EXCHANGE_BTC = 4
ACCOUNT_BTC_FEES = 5
ACCOUNT_USD_FEES = 6

# Virtual account for external transactions
ACCOUNT_EXTERNAL = 99

# Mapping for CSV export (account ID -> display name)
ACCOUNT_ID_TO_NAME = {
    ACCOUNT_BANK: "Bank",
    ACCOUNT_WALLET: "Wallet",
    ACCOUNT_EXCHANGE_USD: "Exchange USD",
    ACCOUNT_EXCHANGE_BTC: "Exchange BTC",
    ACCOUNT_BTC_FEES: "BTC Fees",
    ACCOUNT_USD_FEES: "USD Fees",
    ACCOUNT_EXTERNAL: "External",
}

# Mapping for CSV import (lowercase name -> account ID)
ACCOUNT_NAME_TO_ID = {
    "bank": ACCOUNT_BANK,
    "wallet": ACCOUNT_WALLET,
    "exchange usd": ACCOUNT_EXCHANGE_USD,
    "exchange btc": ACCOUNT_EXCHANGE_BTC,
    "btc fees": ACCOUNT_BTC_FEES,
    "usd fees": ACCOUNT_USD_FEES,
    "external": ACCOUNT_EXTERNAL,
}
