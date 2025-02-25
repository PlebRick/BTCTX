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
# Import logging for error handling and debugging.
import logging

# Import our ORM models that represent the database tables.
from backend.models.account import Account
from backend.models.transaction import Transaction, LedgerEntry

# Configure basic logging (adjust level and handlers as needed for your environment).
logging.basicConfig(level=logging.WARNING)

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
        List[Dict]: A list where each dictionary has the following structure:
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
      - Withdrawals Spent: The total 'proceeds_usd' from Withdrawal transactions where purpose is "Spent".
      - Income Earned: For Deposit transactions with source "Income", the 'cost_basis_usd' represents income.
      - Interest Earned: For Deposit transactions with source "Interest", using 'cost_basis_usd'.
      - Fees: Fees are aggregated by their currency (e.g., USD and BTC are summed separately).

    After processing transactions, it aggregates:
      - Total Gains: Sum of sells proceeds, income earned, and interest earned.
      - Total Losses: Total withdrawals spent, representing outflow losses.

    Notes:
      - String comparisons are case-insensitive to handle variations in data (e.g., "SELL" vs "Sell").
      - Exceptions during Decimal conversion are logged instead of silently ignored.
      - Unexpected fee currencies are logged for investigation.

    Args:
        db (Session): The SQLAlchemy database session.

    Returns:
        Dict: A dictionary containing the calculated values, e.g.:
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
    # Initialize accumulators as Decimals set to zero for precise arithmetic.
    sells_proceeds = Decimal("0.0")
    withdrawals_spent = Decimal("0.0")
    income_earned = Decimal("0.0")
    interest_earned = Decimal("0.0")
    fees_usd = Decimal("0.0")
    fees_btc = Decimal("0.0")

    # Retrieve all transactions from the database in one query.
    transactions = db.query(Transaction).all()

    # Process each transaction to update accumulators based on type and attributes.
    for tx in transactions:
        # Handle Sell transactions: accumulate proceeds if available.
        if tx.type.lower() == "sell" and tx.proceeds_usd is not None:
            try:
                # Note: If tx.proceeds_usd is already numeric, consider Decimal(tx.proceeds_usd) directly.
                sells_proceeds += Decimal(str(tx.proceeds_usd))
            except Exception as e:
                logging.warning(f"Error converting proceeds_usd for Sell transaction {tx.id}: {e}")

        # Handle Withdrawal transactions with purpose "Spent": accumulate proceeds.
        if tx.type.lower() == "withdrawal" and tx.purpose.lower() == "spent" and tx.proceeds_usd is not None:
            try:
                withdrawals_spent += Decimal(str(tx.proceeds_usd))
            except Exception as e:
                logging.warning(f"Error converting proceeds_usd for Withdrawal transaction {tx.id}: {e}")

        # Handle Deposit transactions with source "Income": accumulate positive cost basis as income.
        if tx.type.lower() == "deposit" and tx.source.lower() == "income":
            try:
                if tx.cost_basis_usd is not None and Decimal(str(tx.cost_basis_usd)) > 0:
                    income_earned += Decimal(str(tx.cost_basis_usd))
            except Exception as e:
                logging.warning(f"Error converting cost_basis_usd for Income Deposit transaction {tx.id}: {e}")

        # Handle Deposit transactions with source "Interest": accumulate positive cost basis as interest.
        if tx.type.lower() == "deposit" and tx.source.lower() == "interest":
            try:
                if tx.cost_basis_usd is not None and Decimal(str(tx.cost_basis_usd)) > 0:
                    interest_earned += Decimal(str(tx.cost_basis_usd))
            except Exception as e:
                logging.warning(f"Error converting cost_basis_usd for Interest Deposit transaction {tx.id}: {e}")

        # Aggregate fees by currency, logging unexpected currencies.
        if tx.fee_amount is not None and tx.fee_currency is not None:
            try:
                fee_amt = Decimal(str(tx.fee_amount))
                currency = tx.fee_currency.lower()
                if currency == "usd":
                    fees_usd += fee_amt
                elif currency == "btc":
                    fees_btc += fee_amt
                else:
                    logging.warning(f"Unexpected fee currency '{tx.fee_currency}' for transaction {tx.id}")
            except Exception as e:
                logging.warning(f"Error converting fee_amount for transaction {tx.id}: {e}")

    # Calculate total gains as the sum of all inflows.
    total_gains = sells_proceeds + income_earned + interest_earned
    # Define total losses as the sum of outflows (currently only withdrawals spent).
    total_losses = withdrawals_spent

    # Return all computed values in a structured dictionary.
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