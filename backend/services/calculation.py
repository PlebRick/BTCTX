"""
backend/services/calculation.py

Refactored aggregator to separate short-term vs. long-term gains and losses.
Removed old aggregator fields that are no longer used.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal, ROUND_HALF_DOWN
from typing import List, Dict
from sqlalchemy.orm import Session
from backend.models.transaction import BitcoinLot
import logging
from backend.models.account import Account
from backend.models.transaction import Transaction, LedgerEntry
from backend.models.transaction import LotDisposal

logging.basicConfig(level=logging.WARNING)

def get_account_balance(db: Session, account_id: int) -> Decimal:
    total = (
        db.query(func.sum(LedgerEntry.amount))
          .filter(LedgerEntry.account_id == account_id)
          .scalar()
    )
    return total or Decimal("0.0")


def get_all_account_balances(db: Session) -> List[Dict]:
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

def get_average_cost_basis(db: Session) -> Decimal:
    """
    Returns the average USD cost basis per BTC across all current lots.
    Total leftover cost basis divided by total remaining BTC, rounded to 2 decimals for display.
    """
    lots = db.query(BitcoinLot).filter(BitcoinLot.remaining_btc > 0).all()
    total_btc_remaining = Decimal("0")
    total_cost_basis_remaining = Decimal("0")

    for lot in lots:
        fraction_left = (lot.remaining_btc / lot.total_btc).quantize(Decimal("0.00000001"))
        leftover_cost_basis = (lot.cost_basis_usd * fraction_left).quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)
        total_btc_remaining += lot.remaining_btc
        total_cost_basis_remaining += leftover_cost_basis

    if total_btc_remaining == 0:
        return Decimal("0")
    
    return (total_cost_basis_remaining / total_btc_remaining).quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)


def get_gains_and_losses(db: Session) -> dict:
    """
    Calculate total realized gains and losses from all disposals.
    """
    disposals = db.query(LotDisposal).all()
    short_term_gains = Decimal("0")
    short_term_losses = Decimal("0")
    long_term_gains = Decimal("0")
    long_term_losses = Decimal("0")

    for disposal in disposals:
        gain = disposal.realized_gain_usd
        if gain > 0:
            if disposal.holding_period == "SHORT":
                short_term_gains += gain
            else:
                long_term_gains += gain
        elif gain < 0:
            if disposal.holding_period == "SHORT":
                short_term_losses += -gain
            else:
                long_term_losses += -gain

    return {
        "sells_proceeds": 0,  # Placeholder, calculate if needed
        "withdrawals_spent": 0,  # Placeholder, calculate if needed
        "income_earned": db.query(func.sum(Transaction.cost_basis_usd)).filter(Transaction.type == "Deposit").scalar() or 0,
        "income_btc": db.query(func.sum(Transaction.amount)).filter(Transaction.type == "Deposit", Transaction.fee_currency == "BTC").scalar() or 0,
        "interest_earned": 0,  # Placeholder
        "interest_btc": 0,  # Placeholder
        "rewards_earned": 0,  # Placeholder
        "rewards_btc": 0,  # Placeholder
        "gifts_received": 0,  # Placeholder
        "gifts_btc": 0,  # Placeholder
        "fees": {
            "USD": 0,
            "BTC": db.query(func.sum(Transaction.fee_amount)).filter(Transaction.fee_currency == "BTC").scalar() or 0
        },
        "total_income": db.query(func.sum(Transaction.cost_basis_usd)).filter(Transaction.type == "Deposit").scalar() or 0,
        "total_losses": 0,  # Placeholder
        "short_term_gains": float(short_term_gains.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "short_term_losses": float(short_term_losses.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "short_term_net": float((short_term_gains - short_term_losses).quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "long_term_gains": float(long_term_gains.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "long_term_losses": float(long_term_losses.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "long_term_net": float((long_term_gains - long_term_losses).quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "total_net_capital_gains": float((short_term_gains + long_term_gains - short_term_losses - long_term_losses).quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN))
    }

