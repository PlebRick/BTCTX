"""
backend/services/calculation.py

Refactored aggregator to separate short-term vs. long-term gains and losses.
Removed old aggregator fields that are no longer used.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal, ROUND_HALF_DOWN
from typing import List, Dict
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
    Calculate various gains and losses across all transactions and disposals.
    Tracks positive short-term vs. long-term gains separately from losses,
    then computes net amounts. Includes income, fees, and other fields.
    """
    # Aggregators for existing usage
    sells_proceeds = Decimal("0.0")
    withdrawals_spent = Decimal("0.0")
    income_earned = Decimal("0.0")
    income_btc = Decimal("0.0")
    interest_earned = Decimal("0.0")
    interest_btc = Decimal("0.0")
    rewards_earned = Decimal("0.0")
    rewards_btc = Decimal("0.0")
    gifts_received = Decimal("0.0")
    gifts_btc = Decimal("0.0")
    fees_usd = Decimal("0.0")
    fees_btc = Decimal("0.0")

    # Gains vs. Losses fields
    short_term_gains = Decimal("0.0")
    short_term_losses = Decimal("0.0")
    long_term_gains = Decimal("0.0")
    long_term_losses = Decimal("0.0")

    # Aggregate LotDisposal entries (e.g., from fee disposals)
    disposals = db.query(LotDisposal).all()
    for disposal in disposals:
        gain = disposal.realized_gain_usd
        holding_period = disposal.holding_period or "SHORT"  # Use schema value, fallback to "SHORT"
        if gain > 0:
            if holding_period == "SHORT":
                short_term_gains += gain
            else:
                long_term_gains += gain
        elif gain < 0:
            if holding_period == "SHORT":
                short_term_losses += -gain
            else:
                long_term_losses += -gain

    # Pull all transactions for additional aggregations
    transactions = db.query(Transaction).all()  # Changed to Transaction

    for tx in transactions:
        # SELL => add to sells_proceeds
        if tx.type.lower() == "sell" and tx.proceeds_usd is not None:
            try:
                sells_proceeds += Decimal(str(tx.proceeds_usd))
            except Exception as e:
                logging.warning(f"Error converting proceeds_usd for Sell txn {tx.id}: {e}")

        # WITHDRAWAL (Spent) => add to withdrawals_spent
        if (
            tx.type.lower() == "withdrawal"
            and (tx.purpose or "").lower() == "spent"
            and tx.proceeds_usd is not None
        ):
            try:
                withdrawals_spent += Decimal(str(tx.proceeds_usd))
            except Exception as e:
                logging.warning(f"Error converting proceeds_usd for Withdrawal txn {tx.id}: {e}")

        # DEPOSIT (Income)
        if (
            tx.type.lower() == "deposit"
            and (tx.source or "").lower() == "income"
            and tx.cost_basis_usd is not None
            and tx.amount is not None
        ):
            try:
                cb = Decimal(str(tx.cost_basis_usd))
                amt = Decimal(str(tx.amount))
                if cb > 0:
                    income_earned += cb
                if amt > 0:
                    income_btc += amt
            except Exception as e:
                logging.warning(f"Error converting cost_basis_usd for Income Deposit txn {tx.id}: {e}")

        # DEPOSIT (Interest)
        if (
            tx.type.lower() == "deposit"
            and (tx.source or "").lower() == "interest"
            and tx.cost_basis_usd is not None
            and tx.amount is not None
        ):
            try:
                cb = Decimal(str(tx.cost_basis_usd))
                amt = Decimal(str(tx.amount))
                if cb > 0:
                    interest_earned += cb
                if amt > 0:
                    interest_btc += amt
            except Exception as e:
                logging.warning(f"Error converting cost_basis_usd for Interest Deposit txn {tx.id}: {e}")

        # DEPOSIT (Reward)
        if (
            tx.type.lower() == "deposit"
            and (tx.source or "").lower() == "reward"
            and tx.cost_basis_usd is not None
            and tx.amount is not None
        ):
            try:
                cb = Decimal(str(tx.cost_basis_usd))
                amt = Decimal(str(tx.amount))
                if cb > 0:
                    rewards_earned += cb
                if amt > 0:
                    rewards_btc += amt
            except Exception as e:
                logging.warning(f"Error converting cost_basis_usd for Reward Deposit txn {tx.id}: {e}")

        # DEPOSIT (Gift)
        if (
            tx.type.lower() == "deposit"
            and (tx.source or "").lower() == "gift"
            and tx.cost_basis_usd is not None
            and tx.amount is not None
        ):
            try:
                cb = Decimal(str(tx.cost_basis_usd))
                amt = Decimal(str(tx.amount))
                if cb > 0:
                    gifts_received += cb
                if amt > 0:
                    gifts_btc += amt
            except Exception as e:
                logging.warning(f"Error converting cost_basis_usd for Gift Deposit txn {tx.id}: {e}")

        # FEES
        if tx.fee_amount is not None and tx.fee_currency is not None:
            try:
                fee_amt = Decimal(str(tx.fee_amount))
                currency = tx.fee_currency.lower()
                if currency == "usd":
                    fees_usd += fee_amt
                elif currency == "btc":
                    fees_btc += fee_amt
            except Exception as e:
                logging.warning(f"Error converting fee_amount for txn {tx.id}: {e}")

        # Gains/Losses from Transactions (Sells and Spent Withdrawals)
        if tx.realized_gain_usd is not None:
            try:
                rg = Decimal(str(tx.realized_gain_usd))
                is_disposal = False
                if tx.type.lower() == "sell":
                    is_disposal = True
                elif tx.type.lower() == "withdrawal" and (tx.purpose or "").lower() == "spent":
                    is_disposal = True

                if is_disposal and rg != Decimal("0.0"):
                    hp = (tx.holding_period or "").upper()
                    if hp == "SHORT":
                        if rg > 0:
                            short_term_gains += rg
                        else:
                            short_term_losses += abs(rg)
                    elif hp == "LONG":
                        if rg > 0:
                            long_term_gains += rg
                        else:
                            long_term_losses += abs(rg)
            except Exception as e:
                logging.warning(f"Error converting realized_gain_usd for txn {tx.id}: {e}")

    # Summations & Return
    total_income = income_earned + interest_earned + rewards_earned
    total_losses = withdrawals_spent
    short_term_net = short_term_gains - short_term_losses
    long_term_net = long_term_gains - long_term_losses
    total_net_capital_gains = short_term_net + long_term_net

    return {
        "sells_proceeds": float(sells_proceeds.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "withdrawals_spent": float(withdrawals_spent.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "income_earned": float(income_earned.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "income_btc": float(income_btc.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "interest_earned": float(interest_earned.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "interest_btc": float(interest_btc.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "rewards_earned": float(rewards_earned.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "rewards_btc": float(rewards_btc.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "gifts_received": float(gifts_received.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "gifts_btc": float(gifts_btc.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "fees": {
            "USD": float(fees_usd.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
            "BTC": float(fees_btc.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        },
        "total_income": float(total_income.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "total_losses": float(total_losses.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "short_term_gains": float(short_term_gains.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "short_term_losses": float(short_term_losses.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "short_term_net": float(short_term_net.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "long_term_gains": float(long_term_gains.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "long_term_losses": float(long_term_losses.quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "long_term_net": float((long_term_gains - long_term_losses).quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)),
        "total_net_capital_gains": float((short_term_gains + long_term_gains - short_term_losses - long_term_losses).quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN))
    }

