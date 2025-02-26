"""
backend/services/calculation.py

This module implements the core calculation logic for BitcoinTX.
It includes functions to:
  - Calculate account balances by summing ledger entries.
  - Calculate gains and losses based on transaction data.

The gains and losses calculations include:
  - Proceeds from Sell transactions on the exchange.
  - Proceeds from Withdrawals with a purpose of "Spent".
  - Income earned (from Deposit transactions with source "Income".
  - Interest earned (from Deposit transactions with source "Interest".
  - Aggregation of fees (grouped by currency).

These functions return Decimal values (or dictionaries containing Decimals)
so that they can later be formatted or converted to floats for display.

Compatible with the new Docker + central /api structure:
This file has no direct knowledge of API routes or trailing slashes.
Those details are handled in the 'backend/routers/calculation.py' router.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import List, Dict
import logging

# Import the ORM models for accounts, transactions, ledger entries
from backend.models.account import Account
from backend.models.transaction import Transaction, LedgerEntry

logging.basicConfig(level=logging.WARNING)

def get_account_balance(db: Session, account_id: int) -> Decimal:
    """
    Calculate the balance for a given account by summing all associated LedgerEntry amounts.

    Args:
        db (Session): The SQLAlchemy database session used for executing queries.
        account_id (int): The unique identifier of the account whose balance is to be calculated.

    Returns:
        Decimal: The computed balance. If no ledger entries are found, returns Decimal("0.0").
    """
    total = (
        db.query(func.sum(LedgerEntry.amount))
          .filter(LedgerEntry.account_id == account_id)
          .scalar()
    )
    return total or Decimal("0.0")

def get_all_account_balances(db: Session) -> List[Dict]:
    """
    Calculate the balances for all accounts in the system.

    - Retrieves each Account.
    - Uses 'get_account_balance' for each to sum associated ledger entries.
    - Returns a list of dicts with {account_id, name, currency, balance}.

    Args:
        db (Session): The active SQLAlchemy database session.

    Returns:
        List[Dict]: One dictionary per account, e.g.:
                    {
                      "account_id": int,
                      "name": str,
                      "currency": str,
                      "balance": Decimal
                    }
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
    Calculate various gains and losses across all transactions.

    This function processes each transaction to compute:
      - Sells Proceeds: total 'proceeds_usd' for 'Sell' transactions.
      - Withdrawals Spent: total 'proceeds_usd' for 'Withdrawal' transactions (purpose='Spent').
      - Income Earned: 'cost_basis_usd' for 'Deposit' (source='Income').
      - Interest Earned: 'cost_basis_usd' for 'Deposit' (source='Interest').
      - Fees: aggregated per currency (USD, BTC).
      - Total Gains: sum of sells proceeds, income earned, and interest earned.
      - Total Losses: sum of withdrawals spent.

    Returns:
        Dict: A structured dictionary of Decimal values, e.g.:
              {
                  "sells_proceeds": Decimal(...),
                  "withdrawals_spent": Decimal(...),
                  "income_earned": Decimal(...),
                  "interest_earned": Decimal(...),
                  "fees": {
                      "USD": Decimal(...),
                      "BTC": Decimal(...)
                  },
                  "total_gains": Decimal(...),
                  "total_losses": Decimal(...)
              }
    """
    sells_proceeds = Decimal("0.0")
    withdrawals_spent = Decimal("0.0")
    income_earned = Decimal("0.0")
    interest_earned = Decimal("0.0")
    fees_usd = Decimal("0.0")
    fees_btc = Decimal("0.0")

    transactions = db.query(Transaction).all()
    for tx in transactions:
        # SELL
        if tx.type.lower() == "sell" and tx.proceeds_usd is not None:
            try:
                sells_proceeds += Decimal(str(tx.proceeds_usd))
            except Exception as e:
                logging.warning(f"Error converting proceeds_usd for Sell txn {tx.id}: {e}")

        # WITHDRAWAL (Spent)
        if (tx.type.lower() == "withdrawal"
            and (tx.purpose or "").lower() == "spent"
            and tx.proceeds_usd is not None):
            try:
                withdrawals_spent += Decimal(str(tx.proceeds_usd))
            except Exception as e:
                logging.warning(f"Error converting proceeds_usd for Withdrawal txn {tx.id}: {e}")

        # DEPOSIT (Income)
        if (tx.type.lower() == "deposit"
            and (tx.source or "").lower() == "income"
            and tx.cost_basis_usd is not None):
            try:
                if Decimal(str(tx.cost_basis_usd)) > 0:
                    income_earned += Decimal(str(tx.cost_basis_usd))
            except Exception as e:
                logging.warning(f"Error converting cost_basis_usd for Income Deposit txn {tx.id}: {e}")

        # DEPOSIT (Interest)
        if (tx.type.lower() == "deposit"
            and (tx.source or "").lower() == "interest"
            and tx.cost_basis_usd is not None):
            try:
                if Decimal(str(tx.cost_basis_usd)) > 0:
                    interest_earned += Decimal(str(tx.cost_basis_usd))
            except Exception as e:
                logging.warning(f"Error converting cost_basis_usd for Interest Deposit txn {tx.id}: {e}")

        # FEES
        if tx.fee_amount is not None and tx.fee_currency is not None:
            try:
                fee_amt = Decimal(str(tx.fee_amount))
                currency = tx.fee_currency.lower()
                if currency == "usd":
                    fees_usd += fee_amt
                elif currency == "btc":
                    fees_btc += fee_amt
                else:
                    logging.warning(f"Unexpected fee currency '{tx.fee_currency}' for txn {tx.id}")
            except Exception as e:
                logging.warning(f"Error converting fee_amount for txn {tx.id}: {e}")

    total_gains = sells_proceeds + income_earned + interest_earned
    total_losses = withdrawals_spent

    return {
        "sells_proceeds": sells_proceeds,
        "withdrawals_spent": withdrawals_spent,
        "income_earned": income_earned,
        "interest_earned": interest_earned,
        "fees": {
            "USD": fees_usd,
            "BTC": fees_btc,
        },
        "total_gains": total_gains,
        "total_losses": total_losses,
    }
