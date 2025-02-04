import requests

# Define the API URL (adjust for your local setup)
API_URL = "http://127.0.0.1:8000/api/transactions/"

# Sample transaction data
transaction_data = {
    "account_id": 1,
    "type": "Deposit",
    "amount_usd": 1000.00,
    "amount_btc": 0.0,
    "timestamp": "2025-02-04T12:30:00",
    "source": "Income",
    "purpose": None,
    "fee": {"currency": "USD", "amount": 0.50}
}

# Send POST request to the API
response = requests.post(API_URL, json=transaction_data)

# Print the response
print("Response status code:", response.status_code)
print("Response JSON:", response.json())