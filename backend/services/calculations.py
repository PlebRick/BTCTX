"""
backend/services/calculation.api.py

This module implements the core calculation logic for BitcoinTX.
It includes functions to:
  - Calculate account balances by summing ledger entries.
  - Calculate gains and losses based on transaction data.
  
The gains and losses calculations include:
  - Proceeds from Sell transactions on the exchange.
  - Proceeds from Withdrawals with a purpose of "Spent".
  - Income earned (from Deposit transactions with source "Income").
  - Interest earned (from Deposit transactions with source "Interest").
  - Aggregation of fees (grouped by currency).

These functions return Decimal values (or dictionaries containing Decimals)
so that they can later be formatted or converted to floats for display.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import List, Dict

# Import our ORM models
from backend.models.account import Account
from backend.models.transaction import Transaction, LedgerEntry

def get_account_balance(db: Session, account_id: int) -> Decimal:
    """
    Calculate the balance for a given account by summing all LedgerEntry amounts.
    
    Args:
      db (Session): The SQLAlchemy database session.
      account_id (int): The ID of the account to calculate.
    
    Returns:
      Decimal: The account balance (0.0 if no entries exist).
    """
    total = db.query(func.sum(LedgerEntry.amount))\
              .filter(LedgerEntry.account_id == account_id)\
              .scalar()
    return total or Decimal("0.0")

def get_all_account_balances(db: Session) -> List[Dict]:
    """
    Calculate balances for all accounts in the system.
    
    Args:
      db (Session): The SQLAlchemy database session.
    
    Returns:
      List[dict]: Each dictionary contains 'account_id', 'name', 'currency', and 'balance'.
    """
    accounts = db.query(Account).all()
    results = []
    for account in accounts:
        balance = get_account_balance(db, account.id)
        results.append({
            "account_id": account.id,
            "name": account.name,
            "currency": account.currency,
            "balance": balance
        })
    return results

def get_gains_and_losses(db: Session) -> Dict:
    """
    Calculate various gains and losses across transactions.
    
    The calculations include:
      - Sells Proceeds: Sum of 'proceeds_usd' for transactions of type "Sell".
      - Withdrawals Spent: Sum of 'proceeds_usd' for Withdrawal transactions with purpose "Spent".
      - Income Earned: For Deposit transactions with source "Income", we use the 'cost_basis_usd'
                        (assuming that represents the monetary value of the deposit).
      - Interest Earned: For Deposit transactions with source "Interest", similarly using 'cost_basis_usd'.
      - Fees: Aggregated fee amounts, grouped by 'fee_currency'.
    
    Returns:
      dict: A dictionary with keys for each category plus total gains and total losses.
            For example:
            {
              "sells_proceeds": Decimal(...),
              "withdrawals_spent": Decimal(...),
              "income_earned": Decimal(...),
              "interest_earned": Decimal(...),
              "fees": { "USD": Decimal(...), "BTC": Decimal(...) },
              "total_gains": Decimal(...),
              "total_losses": Decimal(...)
            }
    """
    # Initialize sums to zero
    sells_proceeds = Decimal("0.0")
    withdrawals_spent = Decimal("0.0")
    income_earned = Decimal("0.0")
    interest_earned = Decimal("0.0")
    fees_usd = Decimal("0.0")
    fees_btc = Decimal("0.0")
    
    # Retrieve all transactions
    transactions = db.query(Transaction).all()
    
    for tx in transactions:
        # For Sell transactions, add proceeds_usd if available.
        if tx.type == "Sell" and tx.proceeds_usd is not None:
            try:
                sells_proceeds += Decimal(str(tx.proceeds_usd))
            except Exception:
                pass

        # For Withdrawal transactions with purpose "Spent", add proceeds_usd.
        if tx.type == "Withdrawal" and tx.purpose == "Spent" and tx.proceeds_usd is not None:
            try:
                withdrawals_spent += Decimal(str(tx.proceeds_usd))
            except Exception:
                pass

        # For Deposit transactions with source "Income", use cost_basis_usd.
        if tx.type == "Deposit" and tx.source == "Income":
            try:
                if tx.cost_basis_usd is not None and Decimal(str(tx.cost_basis_usd)) > 0:
                    income_earned += Decimal(str(tx.cost_basis_usd))
            except Exception:
                pass

        # For Deposit transactions with source "Interest", use cost_basis_usd.
        if tx.type == "Deposit" and tx.source == "Interest":
            try:
                if tx.cost_basis_usd is not None and Decimal(str(tx.cost_basis_usd)) > 0:
                    interest_earned += Decimal(str(tx.cost_basis_usd))
            except Exception:
                pass

        # Aggregate fees by fee_currency
        if tx.fee_amount is not None:
            try:
                fee_amt = Decimal(str(tx.fee_amount))
                if tx.fee_currency == "USD":
                    fees_usd += fee_amt
                elif tx.fee_currency == "BTC":
                    fees_btc += fee_amt
            except Exception:
                pass

    # Total gains could be defined as proceeds plus income and interest.
    total_gains = sells_proceeds + income_earned + interest_earned
    # Total losses: Here we assume withdrawals (Spent) represent outflow losses.
    total_losses = withdrawals_spent

    return {
        "sells_proceeds": sells_proceeds,
        "withdrawals_spent": withdrawals_spent,
        "income_earned": income_earned,
        "interest_earned": interest_earned,
        "fees": {
            "USD": fees_usd,
            "BTC": fees_btc
        },
        "total_gains": total_gains,
        "total_losses": total_losses
    }
