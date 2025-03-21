# backend/services/reports/reporting_core.py

from datetime import datetime, timezone
from typing import Dict, Any, List
from decimal import Decimal, ROUND_HALF_DOWN

from sqlalchemy.orm import Session
from backend.models.transaction import (
    Transaction,
    BitcoinLot,
    LotDisposal,
)
from backend.models.account import Account
from backend.services.transaction import (
    recalculate_all_transactions,
    recalculate_subsequent_transactions,  # We'll use partial-lot approach
    get_all_transactions,
)
import logging

logger = logging.getLogger(__name__)


def generate_report_data(db: Session, year: int) -> Dict[str, Any]:
    """
    Generates a comprehensive dictionary of data for the specified tax year
    (YYYY) to be used by different PDF reports (e.g., complete_tax_report,
    ScheduleD, form_8949).

    Includes:
      - Beginning-of-year balances (start_of_year_balances).
      - A one-line summary of capital gains (short vs. long).
      - An income summary for BTC deposits with source=Income/Reward/Interest.
      - An asset summary, extended to handle multiple assets (if any).
      - End-of-year balances for each lot still held.
      - Summaries of capital gains transactions, both “header-level” and
        fully granular partial-lot detail for 8949/ScheduleD.
      - Lists for “Income Transactions,” “Gifts/Donations/Lost,” “Expenses,” etc.
      - Data sources used in your transactions.

    Steps:
      1) First gather 'start_of_year_balances' by partial-lot re-lot up to Jan 1,
         then revert to normal state for the rest of the year.
      2) Then do 'scorched earth' re-lot for the entire year, build normal aggregator data.
      3) Return everything in a final dict.
    """
    logger.info(f"Begin building report data for tax_year={year}")

    # 1) Gather beginning-of-year balances
    #    => partial-lot approach up to (year, 1, 1)
    start_of_year_data = _build_start_of_year_balances(db, year)

    # 2) Re-lot everything from scratch for the entire year
    recalculate_all_transactions(db)

    # 3) Filter transactions for that tax year
    start_dt = datetime(year, 1, 1, tzinfo=timezone.utc)
    end_dt   = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    txns = (
        db.query(Transaction)
        .filter(Transaction.timestamp >= start_dt, Transaction.timestamp <= end_dt)
        .order_by(Transaction.timestamp.asc(), Transaction.id.asc())
        .all()
    )

    # 4) Build each needed section
    gains_dict = _build_capital_gains_summary(txns)
    income_dict = _build_income_summary(txns)
    asset_list = _build_asset_summary(db, end_dt)
    eoy_list = _build_end_of_year_balances(db, end_dt)
    cap_gain_txs_summary = _build_capital_gains_transactions_summary(txns)
    cap_gain_txs_detail  = _build_capital_gains_transactions_detailed(db, txns)
    income_txs   = _build_income_transactions(txns)
    gifts_lost   = _build_gifts_donations_lost(txns)
    expense_list = _build_expenses_list(txns)
    data_sources_list = _gather_data_sources(txns)

    # 5) Construct final dictionary
    result = {
        "tax_year": year,
        "report_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "period": f"{year}-01-01 to {year}-12-31",

        # NEW: store beginning-of-year data
        "start_of_year_balances": start_of_year_data,

        "capital_gains_summary": gains_dict,       # short vs long aggregated
        "income_summary": income_dict,             # deposit-based Income/Reward/Interest
        "asset_summary": asset_list,               # multi-asset or just BTC
        "end_of_year_balances": eoy_list,          # leftover BTC lots, etc.

        # Basic "one line per transaction" disposal listing
        "capital_gains_transactions": cap_gain_txs_summary,

        # A fully “granular” partial-lot disposal list (one line per lot disposal)
        "capital_gains_transactions_detailed": cap_gain_txs_detail,

        "income_transactions": income_txs,
        "gifts_donations_lost": gifts_lost,
        "expenses": expense_list,
        "data_sources": data_sources_list,
    }
    return result


def _build_start_of_year_balances(db: Session, year: int) -> List[Dict[str, Any]]:
    """
    Build a list of leftover BTC lots at the moment just before Jan 1 of 'year'.
    Steps:
      1) partial-lot re-lot up to Jan 1 of 'year'.
      2) Query leftover lots with remaining_btc>0.
      3) Possibly add a price as of Jan 1, or set 0. 
      4) Return e.g. [ { "quantity": <float>, "avg_cost_basis": <float>, "value": <float> }, ... ]

    Finally, we do NOT keep the DB in that partial-lot state; we revert by running
    the main 'scorched earth' again in generate_report_data to handle the full year.
    """
    logger.info(f"Calculating start-of-year balances for {year}")

    # We'll do a partial-lot re-lot from <year>-01-01
    # So we gather all transactions from that date forward, remove their usage,
    # effectively leaving behind the leftover from prior years.

    from_dt = datetime(year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    # We call recalculate_subsequent_transactions to remove usage for all tx >= from_dt
    # so the leftover is from prior to that date:
    recalculate_subsequent_transactions(db, from_dt)

    # Now, leftover in the DB is effectively what we had at the stroke of midnight.
    open_lots = (
        db.query(BitcoinLot)
        .filter(BitcoinLot.remaining_btc > 0)
        .all()
    )

    # Suppose we have a notional price on Jan 1
    january1_price = Decimal("16500.00")  # example

    results = []
    for lot in open_lots:
        # fraction if partial-lot was used
        fraction = Decimal("1.0")
        if lot.total_btc and lot.total_btc > 0:
            fraction = lot.remaining_btc / lot.total_btc
        partial_cost = (lot.cost_basis_usd * fraction).quantize(Decimal("0.01"), ROUND_HALF_DOWN)

        if lot.remaining_btc > 0:
            avg_basis = partial_cost / lot.remaining_btc
        else:
            avg_basis = Decimal("0.0")

        cur_value = lot.remaining_btc * january1_price

        results.append({
            "quantity": float(lot.remaining_btc),
            "avg_cost_basis": float(avg_basis),
            "value": float(cur_value)
        })

    logger.info(f"Found {len(results)} open BTC lots as of start of year {year}")
    return results


def _build_capital_gains_summary(txns: List[Transaction]) -> Dict[str, Any]:
    """
    Summarizes short-term vs. long-term gains based on each transaction’s
    realized_gain_usd, cost_basis_usd, proceeds_usd, and holding_period.
    """
    from decimal import Decimal

    total_st_proceeds = Decimal("0.0")
    total_st_basis    = Decimal("0.0")
    total_st_gain     = Decimal("0.0")

    total_lt_proceeds = Decimal("0.0")
    total_lt_basis    = Decimal("0.0")
    total_lt_gain     = Decimal("0.0")

    disposal_count = 0

    for tx in txns:
        if tx.type not in ("Sell", "Withdrawal"):
            continue
        if tx.realized_gain_usd is None:
            continue

        disposal_count += 1
        proceeds = tx.proceeds_usd or Decimal("0.0")
        basis    = tx.cost_basis_usd or Decimal("0.0")
        gain     = tx.realized_gain_usd or Decimal("0.0")

        if tx.holding_period == "LONG":
            total_lt_proceeds += proceeds
            total_lt_basis    += basis
            total_lt_gain     += gain
        else:
            total_st_proceeds += proceeds
            total_st_basis    += basis
            total_st_gain     += gain

    total_proceeds = total_st_proceeds + total_lt_proceeds
    total_basis    = total_st_basis    + total_lt_basis
    net_gains      = total_st_gain     + total_lt_gain

    return {
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


def _build_income_summary(txns: List[Transaction]) -> Dict[str, Any]:
    """
    Summarizes BTC deposit transactions if the deposit's source is
    "Income", "Reward", or "Interest." We only track BTC deposits in
    this app for income, ignoring USD deposit scenarios.
    """
    from decimal import Decimal

    total_income = Decimal("0.0")
    total_reward = Decimal("0.0")
    total_interest = Decimal("0.0")

    for tx in txns:
        if tx.type != "Deposit":
            continue
        if not tx.source:
            continue
        deposit_usd = tx.cost_basis_usd or Decimal("0.0")
        source_lower = tx.source.lower()

        if source_lower == "income":
            total_income += deposit_usd
        elif source_lower == "reward":
            total_reward += deposit_usd
        elif source_lower == "interest":
            total_interest += deposit_usd

    grand_total = total_income + total_reward + total_interest

    return {
        "Income":   float(total_income),
        "Reward":   float(total_reward),
        "Interest": float(total_interest),
        "Total":    float(grand_total),
    }


def _build_asset_summary(db: Session, end_dt: datetime) -> List[Dict[str, Any]]:
    """
    Example multi-asset approach: If only BTC, we'll do a placeholder row for BTC net gains.
    """
    # Hard-coded example:
    btc_profit = 4000.0
    btc_loss   = 0.0
    btc_net    = 4000.0

    return [
        {
            "asset": "BTC",
            "profit": btc_profit,
            "loss": btc_loss,
            "net": btc_net
        }
    ]


def _build_end_of_year_balances(db: Session, end_dt: datetime) -> List[Dict[str, Any]]:
    """
    Summarize leftover BTC from open lots as of 12/31, plus cost basis + approximate market value.
    """
    open_lots = (
        db.query(BitcoinLot)
        .filter(
            BitcoinLot.remaining_btc > 0,
            BitcoinLot.acquired_date <= end_dt
        )
        .order_by(BitcoinLot.acquired_date.asc())
        .all()
    )

    eoy_price = Decimal("94153.13")
    rows = []
    total_btc = Decimal("0.0")
    total_cost = Decimal("0.0")
    total_value = Decimal("0.0")

    for lot in open_lots:
        rem_btc = lot.remaining_btc
        fraction_remaining = Decimal("1")
        if lot.total_btc > 0:
            fraction_remaining = rem_btc / lot.total_btc

        partial_cost = (lot.cost_basis_usd * fraction_remaining).quantize(Decimal("0.01"), ROUND_HALF_DOWN)
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

    rows.append({
        "asset": "Total",
        "quantity": float(total_btc),
        "cost": float(total_cost),
        "value": float(total_value),
        "description": "",
    })
    return rows


def _build_capital_gains_transactions_summary(txns: List[Transaction]) -> List[Dict[str, Any]]:
    """
    One line per Sell/Withdrawal transaction. If partial-lot usage spanned multiple lots,
    lumps them. Great for a simple summary in your PDF.
    """
    results = []
    for tx in txns:
        if tx.type not in ("Sell", "Withdrawal"):
            continue
        if not tx.realized_gain_usd:
            continue

        row = {
            "date_sold": tx.timestamp.isoformat() if tx.timestamp else "",
            "date_acquired": "(multiple lots)",
            "asset": "BTC",
            "amount": float(tx.amount or 0),
            "cost": float(tx.cost_basis_usd or 0),
            "proceeds": float(tx.proceeds_usd or 0),
            "gain_loss": float(tx.realized_gain_usd or 0),
            "holding_period": tx.holding_period or "",
        }
        results.append(row)
    return results


def _build_capital_gains_transactions_detailed(db: Session, txns: List[Transaction]) -> List[Dict[str, Any]]:
    """
    Granular per-lot disposal listing. Perfect for 8949 or line-level detail.
    """
    results: List[Dict[str, Any]] = []

    disposal_txs = [t for t in txns if t.type in ("Sell", "Withdrawal")]
    for tx in disposal_txs:
        lot_usages = tx.lot_disposals
        if not lot_usages:
            continue

        for disp in lot_usages:
            lot = disp.lot
            date_sold_str = tx.timestamp.isoformat() if tx.timestamp else ""
            date_acquired_str = ""
            if lot and lot.acquired_date:
                date_acquired_str = lot.acquired_date.isoformat()

            row = {
                "date_sold": date_sold_str,
                "date_acquired": date_acquired_str,
                "asset": "BTC",
                "amount_disposed": float(disp.disposed_btc or 0),
                "disposal_basis_usd": float(disp.disposal_basis_usd or 0),
                "proceeds_usd_for_that_portion": float(disp.proceeds_usd_for_that_portion or 0),
                "realized_gain_usd": float(disp.realized_gain_usd or 0),
                "holding_period": disp.holding_period or "",
            }
            results.append(row)

    return results


def _build_income_transactions(txns: List[Transaction]) -> List[Dict[str, Any]]:
    """
    All Deposits where source in ("income", "reward", "interest").
    """
    from decimal import Decimal

    results = []
    for tx in txns:
        if tx.type != "Deposit":
            continue
        if not tx.source:
            continue
        source_lower = tx.source.lower()
        if source_lower not in ("income", "reward", "interest"):
            continue

        deposit_usd = tx.cost_basis_usd or Decimal("0.0")
        tx_timestamp = tx.timestamp.isoformat() if tx.timestamp else ""

        if source_lower == "income":
            row_type = "Income"
        elif source_lower == "reward":
            row_type = "Reward"
        else:
            row_type = "Interest"

        row = {
            "date": tx_timestamp,
            "asset": "BTC",  
            "amount": float(tx.amount or 0),
            "value_usd": float(deposit_usd),
            "type": row_type,
            "description": tx.source,
        }
        results.append(row)
    return results


def _build_gifts_donations_lost(txns: List[Transaction]) -> List[Dict[str, Any]]:
    """
    All 'Withdrawal' where purpose in ("Gift","Donation","Lost").
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
                "value_usd": float(tx.proceeds_usd or 0),
                "type": tx.purpose,
            }
            results.append(row)
    return results


def _build_expenses_list(txns: List[Transaction]) -> List[Dict[str, Any]]:
    """
    If purpose=Expenses for a withdrawal, gather them here.
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
    Example: parse transaction.source or account references for data origin.
    """
    sources = set()
    for tx in txns:
        if tx.source:
            sources.add(tx.source)
    return sorted(list(sources))


def _build_start_of_year_balances(db: Session, year: int) -> List[Dict[str, Any]]:
    """
    Build leftover BTC lots at the moment just before Jan 1 of 'year'.
    Approach:
      1) partial-lot re-lot up to (year, 1, 1).
      2) query leftover lots.
      3) add a notional "Jan 1 price" if you want to display a value.

    We'll revert to main logic by calling recalculate_all_transactions(...) later.
    """
    logger.info(f"Building start_of_year_balances for {year}")

    # re-lot from <year>-01-01
    from_dt = datetime(year, 1, 1, tzinfo=timezone.utc)
    recalculate_subsequent_transactions(db, from_dt)

    # leftover lots => how many remain from prior year
    lots = (
        db.query(BitcoinLot)
        .filter(BitcoinLot.remaining_btc > 0)
        .all()
    )

    # example "Jan 1" price
    january1_price = Decimal("16500.00")

    results = []
    for lot in lots:
        # fraction leftover in partial-lot
        fraction = Decimal("1.0")
        if lot.total_btc and lot.total_btc > 0:
            fraction = lot.remaining_btc / lot.total_btc
        partial_cost = (lot.cost_basis_usd * fraction).quantize(Decimal("0.01"), ROUND_HALF_DOWN)

        if lot.remaining_btc > 0:
            avg_basis = partial_cost / lot.remaining_btc
        else:
            avg_basis = Decimal("0.0")

        cur_value = lot.remaining_btc * january1_price

        results.append({
            "quantity": float(lot.remaining_btc),
            "avg_cost_basis": float(avg_basis),
            "value": float(cur_value),
        })

    logger.info(f"Found {len(results)} BTC lots as of start-of-year for {year}")
    return results
