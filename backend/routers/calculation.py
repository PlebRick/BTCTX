"""
backend/routers/calculation.py

This module defines API endpoints for portfolio calculations in BitcoinTX.
It exposes endpoints for:
  - Retrieving a single account's balance.
  - Retrieving all accounts' balances.
  - Retrieving gains and losses calculations.

The underlying logic is implemented in backend/services/calculation.py.
This modular design lets you display each calculation category (or totals) in your frontend.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from sqlalchemy.orm import Session
from decimal import Decimal

# Import calculation functions from our service file.
from backend.services.calculation import (
    get_account_balance,
    get_all_account_balances,
    get_gains_and_losses
)

# Import the database session dependency.
from backend.database import get_db

# Create an APIRouter instance without an internal prefix.
# main.py sets the final prefix ("/api/calculations") and tags.
router = APIRouter(tags=["calculations"])


@router.get("/account/{account_id}/balance")
def api_get_account_balance(account_id: int, db: Session = Depends(get_db)) -> Dict:
    """
    API endpoint to retrieve the balance for a specific account.
    
    This endpoint:
      1. Receives an account ID as a path parameter.
      2. Uses the injected database session to call get_account_balance.
      3. Converts the resulting Decimal balance to a float for JSON serialization.
      4. Returns a dictionary with the account ID and its balance.
    
    Args:
      account_id (int): The unique identifier of the account.
      db (Session): The SQLAlchemy database session provided via dependency injection.
    
    Returns:
      dict: A dictionary in the format:
            { "account_id": <int>, "balance": <float> }
    """
    balance = get_account_balance(db, account_id)
    return {"account_id": account_id, "balance": float(balance)}


@router.get("/accounts/balances")
def api_get_all_account_balances(db: Session = Depends(get_db)) -> List[Dict]:
    """
    API endpoint to retrieve balances for all accounts in the system.
    
    This endpoint:
      1. Uses the database session to call get_all_account_balances, which returns a list of dictionaries.
      2. Iterates over the results and converts each account's balance from Decimal to float.
      3. Returns the updated list for JSON serialization.
    
    Returns:
      List[dict]: Each dictionary includes:
                  { "account_id": <int>, "name": <str>, "currency": <str>, "balance": <float> }
    """
    results = get_all_account_balances(db)
    # Convert each Decimal balance to float for JSON output.
    for item in results:
        item["balance"] = float(item["balance"])
    return results


@router.get("/gains-and-losses")
def api_get_gains_and_losses(db: Session = Depends(get_db)) -> Dict:
    """
    API endpoint to retrieve gains and losses calculations.
    
    This endpoint calculates:
      - Sells proceeds (from Sell transactions)
      - Withdrawals spent proceeds (from Withdrawal transactions with purpose "Spent")
      - Income earned (from Deposit transactions with source "Income")
      - Interest earned (from Deposit transactions with source "Interest")
      - Aggregated fees by currency (e.g., USD, BTC)
      - Total gains (sum of proceeds, income, and interest)
      - Total losses (sum of withdrawals spent)
    
    The function:
      1. Calls get_gains_and_losses to compute these values (returned as Decimals).
      2. Uses a helper function to recursively convert any Decimal values into floats.
      3. Returns the final dictionary suitable for JSON serialization.
    
    Returns:
      dict: A dictionary with keys such as "sells_proceeds", "withdrawals_spent", "income_earned",
            "interest_earned", "fees", "total_gains", and "total_losses", with all numeric values as floats.
    """
    calculations = get_gains_and_losses(db)

    def convert_decimal(item):
        if isinstance(item, Decimal):
            return float(item)
        if isinstance(item, dict):
            return {key: convert_decimal(value) for key, value in item.items()}
        if isinstance(item, list):
            return [convert_decimal(subitem) for subitem in item]
        return item

    return convert_decimal(calculations)
