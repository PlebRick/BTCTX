"""
backend/services/calculation.py

Refactored aggregator to separate short-term vs. long-term gains and losses.
Removed old aggregator fields that are no longer used.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import List, Dict
from sqlalchemy.orm import Session
from backend.models.transaction import BitcoinLot
import logging

from backend.models.account import Account
from backend.models.transaction import Transaction, LedgerEntry

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
    Returns the average USD cost basis per BTC *across all current lots*.
    That is, total leftover cost basis divided by total remaining BTC.

    E.g. if you have two lots:
      • 0.5 BTC left with total cost basis of $10,000 (meaning $20k for the original 1 BTC)
      • 1.0 BTC left with total cost basis of $25,000 (no partial disposal)
    total leftover BTC = 1.5
    total leftover cost basis = (0.5 * 20k) + 25k = 10k + 25k = 35k
    => average cost basis = 35k / 1.5 = ~$23,333.33
    """
    lots = db.query(BitcoinLot).filter(BitcoinLot.remaining_btc > 0).all()

    total_btc_remaining = Decimal("0")
    total_cost_basis_remaining = Decimal("0")

    for lot in lots:
        # fraction_left = how much of the original lot is still left
        # e.g. if total_btc=1.0 but remaining_btc=0.4, fraction_left=0.4
        fraction_left = lot.remaining_btc / lot.total_btc

        # leftover_cost_basis = that fraction of the *original* cost basis
        leftover_cost_basis = lot.cost_basis_usd * fraction_left

        total_btc_remaining += lot.remaining_btc
        total_cost_basis_remaining += leftover_cost_basis

    if total_btc_remaining == 0:
        return Decimal("0")  # or Decimal("0.0") or None, up to your preference

    return total_cost_basis_remaining / total_btc_remaining


def get_gains_and_losses(db: Session) -> Dict:
    """
    Calculate various gains and losses across all transactions.
    We track positive short-term vs. long-term gains separately from losses,
    then compute net amounts. Other fields (income, fees, etc.) remain.
    """
    # ---------------------- Aggregators for existing usage ----------------------
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

    # ---------------------- NEW Gains vs. Losses fields ----------------------
    short_term_gains = Decimal("0.0")
    short_term_losses = Decimal("0.0")
    long_term_gains = Decimal("0.0")
    long_term_losses = Decimal("0.0")

    # Pull all transactions
    transactions = db.query(Transaction).all()

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
                amt = Decimal(str(tx.amount))  # Get BTC amount
                if cb > 0:
                    income_earned += cb
                if amt > 0:
                    income_btc += amt  # Store BTC amount
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
                    interest_btc += amt  # Store BTC amount
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
                    rewards_btc += amt  # Store BTC amount
            except Exception as e:
                logging.warning(f"Error converting cost_basis_usd for Reward Deposit txn {tx.id}: {e}")

        # DEPOSIT (Gift) => tracked but not counted as income
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
                    gifts_btc += amt  # Store BTC amount
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
                else:
                    logging.warning(f"Unexpected fee currency '{tx.fee_currency}' for txn {tx.id}")
            except Exception as e:
                logging.warning(f"Error converting fee_amount for txn {tx.id}: {e}")

        # ------------------ Short vs. Long Gains/Losses (new aggregator) ------------------
        if tx.realized_gain_usd is not None:
            try:
                rg = Decimal(str(tx.realized_gain_usd))
                # Check if transaction is a disposal
                is_disposal = False
                if tx.type.lower() == "sell":
                    is_disposal = True
                elif tx.type.lower() == "withdrawal" and (tx.purpose or "").lower() == "spent":
                    is_disposal = True

                # Split positive vs. negative into gains/losses
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

    # ------------------ Summations & Return ------------------
    # total_income = sum of Income, Interest, Rewards
    total_income = income_earned + interest_earned + rewards_earned

    # total_losses = sum of 'Withdrawals Spent'
    total_losses = withdrawals_spent

    # Net short-term and long-term
    short_term_net = short_term_gains - short_term_losses
    long_term_net = long_term_gains - long_term_losses
    total_net_capital_gains = short_term_net + long_term_net

    return {
        "sells_proceeds": sells_proceeds,
        "withdrawals_spent": withdrawals_spent,
        "income_earned": income_earned,
        "income_btc": income_btc,  # ✅ NEW
        "interest_earned": interest_earned,
        "interest_btc": interest_btc,  # ✅ NEW
        "rewards_earned": rewards_earned,
        "rewards_btc": rewards_btc,  # ✅ NEW
        "gifts_received": gifts_received,
        "gifts_btc": gifts_btc,  # ✅ NEW
        "fees": {
            "USD": fees_usd,
            "BTC": fees_btc,
        },
        "total_income": total_income,
        "total_losses": total_losses,
        "short_term_gains": short_term_gains,
        "short_term_losses": short_term_losses,
        "short_term_net": short_term_net,
        "long_term_gains": long_term_gains,
        "long_term_losses": long_term_losses,
        "long_term_net": long_term_net,
        "total_net_capital_gains": total_net_capital_gains,
    }

