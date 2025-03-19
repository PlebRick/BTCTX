# backend/services/reports/reporting_core.py

from datetime import datetime, timezone
from typing import Dict, Any, List
from decimal import Decimal, ROUND_HALF_DOWN

from sqlalchemy.orm import Session

from backend.models.transaction import Transaction, BitcoinLot, LotDisposal
from backend.services.transaction import (
    recalculate_all_transactions,  # or partial-lot approach
    get_all_transactions,
)
import logging

def generate_report_data(db: Session, year: int) -> Dict[str, Any]:
    """
    1) Re-lot all transactions (scorched earth) or partial-lot if you prefer
    2) Fetch all transactions in the given tax year
    3) Build comprehensive aggregator data for the PDF, e.g.:
       {
         "tax_year": year,
         "report_date": "2025-01-01 09:52",
         "period": "2024-01-01 to 2024-12-31",
         "capital_gains_summary": {...},
         "income_summary": {...},
         "asset_summary": [...],
         "end_of_year_balances": [...],
         "capital_gains_transactions": [...],
         "income_transactions": [...],
         "gifts_donations_lost": [...],
         "expenses": [...],
         "data_sources": [...]
       }
    """
    # 1) Re-lot everything from scratch. (Or partial-lot from 1/1 of that year.)
    # If your system has many prior years, you may want partial-lot from Jan 1 of `year`.
    recalculate_all_transactions(db)  # Or recalculate_subsequent_transactions(...) from 1 Jan

    # 2) Gather all transactions that occur within [year-01-01, year-12-31].
    start_dt = datetime(year, 1, 1, tzinfo=timezone.utc)
    end_dt   = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

    # You could store them in memory
    txns = (
        db.query(Transaction)
        .filter(Transaction.timestamp >= start_dt, Transaction.timestamp <= end_dt)
        .order_by(Transaction.timestamp.asc(), Transaction.id.asc())
        .all()
    )

    # 3) Build each required section. We'll illustrate how to do capital gains summary & a few others.

    # ----------------------------------------------------------------------
    # CAPITAL GAINS
    # ----------------------------------------------------------------------
    # For Sells/Withdrawals that actually disposed BTC, we can sum up from
    # transaction.realized_gain_usd, transaction.cost_basis_usd, transaction.proceeds_usd
    # and also classify short vs. long from transaction.holding_period.

    gains_dict = _build_capital_gains_summary(txns)

    # ----------------------------------------------------------------------
    # INCOME
    # ----------------------------------------------------------------------
    # Typically you’d treat certain Deposits or “source=Mining”/“Reward” as Income.
    # Koinly lumps them in an “Income” category with total USD value.
    # You might also have deposit “source=Salary” or “source=Interest” to sum up, etc.

    income_dict = _build_income_summary(txns)

    # ----------------------------------------------------------------------
    # ASSET SUMMARY
    # ----------------------------------------------------------------------
    # If you only track BTC + USD, you can produce a short table. Otherwise, you could
    # do a partial-lot per asset. For this example, we’ll focus on BTC net gains/loss.
    asset_list = _build_asset_summary(txns)

    # ----------------------------------------------------------------------
    # END OF YEAR BALANCES
    # ----------------------------------------------------------------------
    # Look at all leftover “BitcoinLot.remaining_btc” for that user, and sum it up.
    # Possibly fetch a 12/31 price. You only want lots acquired on or before 12/31. 
    eoy_list = _build_end_of_year_balances(db, end_dt)

    # ----------------------------------------------------------------------
    # DETAILED TRANSACTION LISTS
    # ----------------------------------------------------------------------
    # For the “Comprehensive Tax Report” you might list:
    #   - “Capital Gains Transactions” => every Sell/Withdrawal with partial-lot disposal
    #   - “Income Transactions” => deposits with source=“Income” or so
    #   - “Gifts, Donations & Lost Assets” => withdrawal with “purpose” in (“Gift”,”Donation”,”Lost”)
    #   - “Expenses” => if you track that in “purpose=Expenses”
    # We'll do each one as an example:

    cap_gain_txs = _build_capital_gains_transactions(txns)
    income_txs   = _build_income_transactions(txns)
    gifts_lost   = _build_gifts_donations_lost(txns)
    expense_list = _build_expenses_list(txns)

    # ----------------------------------------------------------------------
    # MISC / DATA SOURCES
    # ----------------------------------------------------------------------
    # You can store references to the “source” field or “account” names used
    # to indicate where data came from. In a multi-exchange environment,
    # you might parse transaction.source or transaction.from_account_id, etc.
    data_sources_list = _gather_data_sources(txns)

    # 4) Construct final dictionary
    result = {
        "tax_year": year,
        "report_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "period": f"{year}-01-01 to {year}-12-31",
        "capital_gains_summary": gains_dict,
        "income_summary": income_dict,
        "asset_summary": asset_list,
        "end_of_year_balances": eoy_list,
        "capital_gains_transactions": cap_gain_txs,
        "income_transactions": income_txs,
        "gifts_donations_lost": gifts_lost,
        "expenses": expense_list,
        "data_sources": data_sources_list,
    }
    return result

# --------------------------------------------------------------------------
# Example helper for capital gains summary
# --------------------------------------------------------------------------

def _build_capital_gains_summary(txns: List[Transaction]) -> Dict[str, Any]:
    """
    Summarize short-term vs. long-term gains by reading each transaction
    that actually disposed BTC. We look at tx.type in ("Sell","Withdrawal")
    *where* partial-lot usage occurred (i.e. realized_gain_usd != 0).
    """
    total_st_proceeds = Decimal("0.0")
    total_st_basis    = Decimal("0.0")
    total_st_gain     = Decimal("0.0")

    total_lt_proceeds = Decimal("0.0")
    total_lt_basis    = Decimal("0.0")
    total_lt_gain     = Decimal("0.0")

    disposal_count = 0

    for tx in txns:
        if tx.type not in ("Sell","Withdrawal"):
            continue
        if tx.realized_gain_usd is None:
            continue  # means no disposal or no partial-lot
        disposal_count += 1
        proceeds = tx.proceeds_usd or Decimal("0.0")
        basis    = tx.cost_basis_usd or Decimal("0.0")
        gain     = tx.realized_gain_usd or Decimal("0.0")

        # Check short vs. long
        if tx.holding_period == "LONG":
            total_lt_proceeds += proceeds
            total_lt_basis    += basis
            total_lt_gain     += gain
        else:
            total_st_proceeds += proceeds
            total_st_basis    += basis
            total_st_gain     += gain

    # For “misc summary” or “other gains” you might have separate logic

    # Net them up
    total_proceeds = total_st_proceeds + total_lt_proceeds
    total_basis    = total_st_basis    + total_lt_basis
    net_gains      = total_st_gain     + total_lt_gain

    result = {
        "number_of_disposals": disposal_count,
        "short_term": {
            "proceeds": float(total_st_proceeds),
            "basis":    float(total_st_basis),
            "gain":     float(total_st_gain),
        },
        "long_term": {
            "proceeds": float(total_lt_proceeds),
            "basis":    float(total_lt_basis),
            "gain":     float(total_lt_gain),
        },
        "total": {
            "proceeds": float(total_proceeds),
            "basis":    float(total_basis),
            "gain":     float(net_gains),
        }
    }
    return result

# --------------------------------------------------------------------------
# Example helper for income summary
# --------------------------------------------------------------------------

def _build_income_summary(txns: List[Transaction]) -> Dict[str, Any]:
    """
    For Koinly-like “Income,” we typically sum deposits with 'source' in
    (“Mining”, “Reward”, “Airdrop”, “Salary”, etc.). If the user is storing
    the USD “proceeds” or “cost_basis_usd” for these, we add them up. Otherwise,
    we might guess a value from a BTC price feed at deposit time.

    This example will:
      - Search for transaction.type == "Deposit"
      - If transaction.source in (“Mining”, “Reward”, “Salary”, “Interest”, “Other?”)
        treat that entire deposit as “income” at the deposit’s BTC * price
    """
    total_income = Decimal("0.0")
    mining_total = Decimal("0.0")
    reward_total = Decimal("0.0")
    other_income = Decimal("0.0")

    # For example, we define:
    income_tags = {"Mining", "Reward", "Salary", "Lending interest", "Other income", "Interest"}

    for tx in txns:
        if tx.type != "Deposit":
            continue
        if not tx.source:
            continue

        # Example: if user typed "Mining" or "Reward" in source
        tag_str = tx.source.lower()
        # We assume we can find a USD value in proceeds_usd or cost_basis_usd, or we do a price lookup
        # For this example, assume cost_basis_usd for a deposit is the “income” value
        deposit_usd_value = tx.cost_basis_usd or Decimal("0.0")

        if "mining" in tag_str:
            mining_total += deposit_usd_value
            total_income += deposit_usd_value
        elif "reward" in tag_str or "interest" in tag_str:
            reward_total += deposit_usd_value
            total_income += deposit_usd_value
        else:
            # If it’s a deposit with some other source, we might treat it as “other income”
            other_income += deposit_usd_value
            total_income += deposit_usd_value

    return {
        "Mining": float(mining_total),
        "Reward": float(reward_total),
        "Other":  float(other_income),
        "Total":  float(total_income),
    }

# --------------------------------------------------------------------------
# Example helper for asset summary
# --------------------------------------------------------------------------

def _build_asset_summary(txns: List[Transaction]) -> List[Dict[str,Any]]:
    """
    Koinly-like “Asset Summary” can show total profit/loss per asset.
    If your system tracks only BTC & USD, we might only show BTC net gains.

    For a multi-asset system, you’d group by transaction currency or partial-lot currency.
    Here we do a minimal approach: everything is mostly BTC or USD.
    We parse each disposal and treat 'BTC' as an asset. 
    If you had additional crypto in the future, you'd group them similarly.
    """
    # Suppose we parse disposal-based gains from the transaction records,
    # grouping by transaction “from_acct.currency” or partial-lot “BTC”.
    # For now, we’ll just say we have "BTC" net from the capital gains summary.

    # A real approach: gather the “_build_capital_gains_summary” data by asset,
    # if you had multiple cryptos.

    # We'll do a single row for BTC using the aggregated results from the capital gains approach
    # You might replicate that logic here, or store it in a shared data structure.

    # For demonstration, let's just do a dummy:
    return [
        {"asset": "BTC", "profit": 32031.99, "loss": 3150.70, "net": 28881.29},
        # If you had more lines for other tokens, they'd appear here
    ]

# --------------------------------------------------------------------------
# Example helper for EOY balances
# --------------------------------------------------------------------------

def _build_end_of_year_balances(db: Session, end_dt: datetime) -> List[Dict[str, Any]]:
    """
    Summarize leftover BTC from open lots as of 12/31, plus cost basis + approximate market value.
    - For each open lot (remaining_btc>0) that was created on or before end_dt,
      we sum them up. We might do a quick “price on 12/31” to get a value in USD.
    """
    # 1) find leftover BTC lots with acquired_date <= end_dt
    open_lots = (
        db.query(BitcoinLot)
        .filter(BitcoinLot.remaining_btc > 0, BitcoinLot.acquired_date <= end_dt)
        .order_by(BitcoinLot.acquired_date.asc())
        .all()
    )

    # 2) sum them up. Optionally do a price lookup (like get_btc_price).
    # For demonstration, let's assume the EOY price was $94,153.13 (like in your example).
    eoy_price = Decimal("94153.13")
    rows = []
    total_btc = Decimal("0.0")
    total_cost = Decimal("0.0")
    total_value = Decimal("0.0")

    for lot in open_lots:
        rem_btc = lot.remaining_btc
        cost_usd = lot.cost_basis_usd
        # If the entire lot is still there, cost_basis_usd is the same. 
        # If partial disposed, we might assume it’s proportional. 
        # In your code, you track cost_basis_usd on the entire original lot. 
        # A more precise approach would scale cost_basis_usd proportionally for partial usage. 
        # For demonstration, let's just store the original leftover fraction.
        fraction_remaining = rem_btc / lot.total_btc if lot.total_btc else Decimal("1")
        partial_cost = (cost_usd * fraction_remaining).quantize(Decimal("0.01"), ROUND_HALF_DOWN)

        cur_value = (rem_btc * eoy_price).quantize(Decimal("0.01"), ROUND_HALF_DOWN)

        rows.append({
            "asset": "BTC (Bitcoin)",
            "quantity": float(rem_btc),
            "cost": float(partial_cost),
            "value": float(cur_value),
            "description": f"@ ${eoy_price} per BTC on {end_dt.date()}"
        })

        total_btc += rem_btc
        total_cost += partial_cost
        total_value += cur_value

    # Optionally add a “Total” row
    rows.append({
        "asset": "Total",
        "quantity": float(total_btc),
        "cost": float(total_cost),
        "value": float(total_value),
        "description": "",
    })
    return rows

# --------------------------------------------------------------------------
# Example “detailed transaction” sections
# --------------------------------------------------------------------------

def _build_capital_gains_transactions(txns: List[Transaction]) -> List[Dict[str,Any]]:
    """
    Return a row for each disposal transaction (Sell/Withdrawal) so the PDF
    can show “Capital Gains Transactions.” 
    We'll re-use the transaction fields:
     - date_sold, date_acquired (the earliest lot?), cost, proceeds, gain, holding_period
    Or you might show multiple lines for partial-lot usage. 
    Here, we'll do a single line per Transaction.
    """
    results = []
    for tx in txns:
        if tx.type not in ("Sell","Withdrawal"):
            continue
        # If no partial-lot usage, skip
        if not tx.realized_gain_usd:
            continue

        # The “date_acquired” is ambiguous if multiple lots. 
        # Your code in `compute_sell_summary_from_disposals` sets `tx.holding_period`,
        # but not the earliest date. If you want each partial-lot, you’d gather from `LotDisposal`.
        # For demonstration, we’ll just show the transaction’s data:

        row = {
            "date_sold": tx.timestamp.isoformat() if tx.timestamp else "",
            "date_acquired": "(multiple lots)",   # or you could parse earliest from partial-lots
            "asset": "BTC",
            "amount": float(tx.amount or 0),
            "cost": float(tx.cost_basis_usd or 0),
            "proceeds": float(tx.proceeds_usd or 0),
            "gain_loss": float(tx.realized_gain_usd or 0),
            "holding_period": tx.holding_period or "",
        }
        results.append(row)
    return results

def _build_income_transactions(txns: List[Transaction]) -> List[Dict[str,Any]]:
    """
    Returns a row for each deposit that looks like “income” based on .source.
    We'll re-use cost_basis_usd or proceed_usd as the income value if present.
    """
    results = []
    for tx in txns:
        if tx.type != "Deposit":
            continue
        if not tx.source:
            continue
        # Heuristic: treat it as “income” if source matches certain patterns
        # We'll just include them all in the “income_transactions”
        row = {
            "date": tx.timestamp.isoformat() if tx.timestamp else "",
            "asset": "BTC",
            "amount": float(tx.amount or 0),
            "value_usd": float(tx.cost_basis_usd or 0),
            "type": "Other" if ("reward" not in tx.source.lower()) else "Reward",
            "description": tx.source,
        }
        results.append(row)
    return results

def _build_gifts_donations_lost(txns: List[Transaction]) -> List[Dict[str,Any]]:
    """
    Pull out all transactions that are 'Withdrawal' where purpose in ("Gift","Donation","Lost").
    This matches Koinly's “Gifts/Donations” or “Lost Assets.”
    """
    results = []
    for tx in txns:
        if tx.type != "Withdrawal":
            continue
        if not tx.purpose:
            continue
        purpose_lower = tx.purpose.lower()
        if purpose_lower in ("gift", "donation", "lost"):
            row = {
                "date": tx.timestamp.isoformat() if tx.timestamp else "",
                "asset": "BTC",
                "amount": float(tx.amount or 0),
                "value_usd": float(tx.proceeds_usd or 0),  # typically 0
                "type": tx.purpose,
            }
            results.append(row)
    return results

def _build_expenses_list(txns: List[Transaction]) -> List[Dict[str,Any]]:
    """
    If you define “purpose=Expenses” or something similar for a withdrawal,
    you can compile them here. 
    For demonstration, we only add a row if purpose == "Expenses".
    """
    results = []
    for tx in txns:
        if tx.type == "Withdrawal" and tx.purpose and tx.purpose.lower() == "expenses":
            row = {
                "date": tx.timestamp.isoformat() if tx.timestamp else "",
                "asset": "BTC",
                "amount": float(tx.amount or 0),
                "value_usd": float(tx.proceeds_usd or 0),
                "type": "Expense",
            }
            results.append(row)
    return results

def _gather_data_sources(txns: List[Transaction]) -> List[str]:
    """
    Example: parse transaction.source or the .from_account_id / .to_account_id
    to guess which exchange/wallet was used. Then we can list them for the final PDF.
    """
    sources = set()
    for tx in txns:
        if tx.source:
            sources.add(tx.source)
        # Alternatively, if you have Account names, you might do:
        #   from_acct = ...
        #   sources.add(from_acct.name)
        # ...
    # Return as a sorted list
    return sorted(list(sources))
