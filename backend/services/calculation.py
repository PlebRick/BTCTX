"""
backend/services/calculation.py

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

# Import SQLAlchemy components for database querying.
from sqlalchemy.orm import Session
from sqlalchemy import func
# Import Decimal for precise arithmetic operations.
from decimal import Decimal
# Import type hints for clarity in function return types.
from typing import List, Dict

# Import our ORM models that represent the database tables.
from backend.models.account import Account
from backend.models.transaction import Transaction, LedgerEntry

def get_account_balance(db: Session, account_id: int) -> Decimal:
    """
    Calculate the balance for a given account by summing all associated LedgerEntry amounts.
    
    In a double-entry accounting system, every transaction generates one or more ledger entries.
    Each entry records a positive (credit) or negative (debit) amount affecting an account.
    By summing the 'amount' field of all LedgerEntry records for a specific account,
    we obtain the current balance of that account.
    
    Args:
      db (Session): The SQLAlchemy database session used for executing queries.
      account_id (int): The unique identifier of the account whose balance is to be calculated.
    
    Returns:
      Decimal: The computed balance as a Decimal. If no ledger entries are found, returns Decimal("0.0").
    """
    total = db.query(func.sum(LedgerEntry.amount))\
              .filter(LedgerEntry.account_id == account_id)\
              .scalar()
    return total or Decimal("0.0")

def get_all_account_balances(db: Session) -> List[Dict]:
    """
    Calculate the balances for all accounts in the system.
    
    This function retrieves every account from the database and computes its balance
    by calling the 'get_account_balance' function. The result is a list of dictionaries,
    with each dictionary containing the account's ID, name, currency, and calculated balance.
    
    Args:
      db (Session): The active SQLAlchemy database session.
    
    Returns:
      List[dict]: A list where each dictionary has the following structure:
                  {
                    "account_id": <int>,
                    "name": <str>,
                    "currency": <str>,
                    "balance": <Decimal>
                  }
    """
    accounts = db.query(Account).all()
    results = []
    for account in accounts:
        # Calculate the balance for each account using the helper function.
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
    Calculate various gains and losses across all transactions.
    
    This function processes each transaction to compute key financial metrics:
      - Sells Proceeds: The total 'proceeds_usd' from transactions of type "Sell".
      - Withdrawals Spent: The total 'proceeds_usd' from Withdrawal transactions where the purpose is "Spent".
      - Income Earned: For Deposit transactions with source "Income", the 'cost_basis_usd' is assumed to represent income.
      - Interest Earned: For Deposit transactions with source "Interest", similarly using 'cost_basis_usd'.
      - Fees: The fees are aggregated by their currency (e.g., USD and BTC are summed separately).
      
    After processing individual transactions, the function aggregates:
      - Total Gains: The sum of sells proceeds, income earned, and interest earned.
      - Total Losses: The total withdrawals spent, representing outflow losses.
    
    Args:
      db (Session): The SQLAlchemy database session.
    
    Returns:
      dict: A dictionary containing the calculated values. For example:
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
    # Initialize accumulators as Decimals set to zero.
    sells_proceeds = Decimal("0.0")
    withdrawals_spent = Decimal("0.0")
    income_earned = Decimal("0.0")
    interest_earned = Decimal("0.0")
    fees_usd = Decimal("0.0")
    fees_btc = Decimal("0.0")
    
    # Retrieve all transactions from the database.
    transactions = db.query(Transaction).all()
    
    # Iterate over each transaction to accumulate values based on its type and attributes.
    for tx in transactions:
        # For Sell transactions, add the proceeds if available.
        if tx.type == "Sell" and tx.proceeds_usd is not None:
            try:
                sells_proceeds += Decimal(str(tx.proceeds_usd))
            except Exception:
                # If conversion fails, skip this transaction.
                pass

        # For Withdrawal transactions with purpose "Spent", add the proceeds.
        if tx.type == "Withdrawal" and tx.purpose == "Spent" and tx.proceeds_usd is not None:
            try:
                withdrawals_spent += Decimal(str(tx.proceeds_usd))
            except Exception:
                pass

        # For Deposit transactions with source "Income", add the cost basis (if positive).
        if tx.type == "Deposit" and tx.source == "Income":
            try:
                if tx.cost_basis_usd is not None and Decimal(str(tx.cost_basis_usd)) > 0:
                    income_earned += Decimal(str(tx.cost_basis_usd))
            except Exception:
                pass

        # For Deposit transactions with source "Interest", add the cost basis (if positive).
        if tx.type == "Deposit" and tx.source == "Interest":
            try:
                if tx.cost_basis_usd is not None and Decimal(str(tx.cost_basis_usd)) > 0:
                    interest_earned += Decimal(str(tx.cost_basis_usd))
            except Exception:
                pass

        # Aggregate fee amounts by their fee currency.
        if tx.fee_amount is not None:
            try:
                fee_amt = Decimal(str(tx.fee_amount))
                if tx.fee_currency == "USD":
                    fees_usd += fee_amt
                elif tx.fee_currency == "BTC":
                    fees_btc += fee_amt
            except Exception:
                pass

    # Define total gains as the sum of sell proceeds, income earned, and interest earned.
    total_gains = sells_proceeds + income_earned + interest_earned
    # Define total losses as the sum of withdrawals spent.
    total_losses = withdrawals_spent

    # Return the computed values in a dictionary.
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
