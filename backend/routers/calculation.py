"""
backend/routers/calculation.api.py

This module defines API endpoints for portfolio calculations in BitcoinTX.
It exposes endpoints for:
  - Retrieving a single account's balance.
  - Retrieving all accounts' balances.
  - Retrieving gains and losses calculations.

The underlying logic is implemented in backend/services/calculation.api.
This modular design lets you display each category (or totals) in your frontend.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from sqlalchemy.orm import Session
from decimal import Decimal

# Import calculation functions from the new calculation module.
from backend.services.calculation.api import (
    get_account_balance,
    get_all_account_balances,
    get_gains_and_losses
)

# Dependency to provide a database session.
from backend.database import get_db

router = APIRouter(prefix="/calculations", tags=["calculations"])

@router.get("/account/{account_id}/balance")
def api_get_account_balance(account_id: int, db: Session = Depends(get_db)) -> Dict:
    """
    API endpoint to retrieve the balance for a specific account.
    
    Args:
      account_id (int): The ID of the account.
      db (Session): Database session (injected).
    
    Returns:
      dict: Contains the account_id and its balance as a float.
    """
    balance = get_account_balance(db, account_id)
    return {"account_id": account_id, "balance": float(balance)}

@router.get("/accounts/balances")
def api_get_all_account_balances(db: Session = Depends(get_db)) -> List[Dict]:
    """
    API endpoint to retrieve balances for all accounts.
    
    Returns:
      List[dict]: Each dictionary includes account_id, name, currency, and balance (as a float).
    """
    results = get_all_account_balances(db)
    # Convert Decimal balances to float for JSON serialization.
    for item in results:
        item["balance"] = float(item["balance"])
    return results

@router.get("/gains-and-losses")
def api_get_gains_and_losses(db: Session = Depends(get_db)) -> Dict:
    """
    API endpoint to retrieve gains and losses calculations.
    
    This includes:
      - Sells proceeds (from Sell transactions)
      - Withdrawals spent proceeds (from Withdrawal transactions with purpose "Spent")
      - Income earned (from Deposit transactions with source "Income")
      - Interest earned (from Deposit transactions with source "Interest")
      - Aggregated fees by currency
      - Total gains and total losses
    
    Returns:
      dict: A dictionary with each category, with Decimal values converted to float.
    """
    calculations = get_gains_and_losses(db)

    def convert_decimal(item):
        """
        Recursively convert Decimal values in a data structure to float.
        """
        if isinstance(item, Decimal):
            return float(item)
        if isinstance(item, dict):
            return {key: convert_decimal(value) for key, value in item.items()}
        if isinstance(item, list):
            return [convert_decimal(subitem) for subitem in item]
        return item

    return convert_decimal(calculations)
