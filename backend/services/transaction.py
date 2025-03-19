"""
backend/services/transaction.py

Core logic for BitcoinTX with a hybrid double-entry:
 - Single-Entry inputs (type, amount, from_account, to_account, etc.)
 - Multi-line LedgerEntry creation for same-currency double-entry
 - Cross-currency Buy/Sell skip net-zero checks for a simpler personal ledger
 - BTC FIFO logic for sells/withdrawals
 - Transfer logic that splits partial-lots, only disposing fee portion

Final Version Tailored for Hybrid BitcoinTX:
 - Deposits/Withdrawals: one-sided if external=99
 - Transfer: net-zero required if same currency
 - Buy/Sell: from=3->4 or 4->3, skip net-zero checks to avoid cross-currency mismatch
 - Fee rules: Buy/Sell => fee=USD, Transfer => fee matches from_acct currency
 - Holding period (SHORT/LONG) is always set for partial-lot disposals.

Implementation Note (Approach #2, "Scorched Earth" for Recalculating):
 - After editing a transaction, we remove *all* ledger entries, partial-lot disposals,
   and BitcoinLots, then re-build them in strict chronological order (timestamp, id).
 - This ensures any backdated or changed transaction re-lots all subsequent data.
 - This is acceptable for a single-user system with a relatively small dataset.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_DOWN
from backend.models.transaction import (Transaction, LedgerEntry, BitcoinLot, LotDisposal)
from backend.models.account import Account
from backend.schemas.transaction import TransactionCreate
from collections import defaultdict
from fastapi import HTTPException
from typing import Optional
import requests
import logging

# --------------------------------------------------------------------------------
# Public Functions
# --------------------------------------------------------------------------------

def get_all_transactions(db: Session):
    """
    Return all Transactions, typically ordered descending by timestamp.
    This function simply retrieves all Transaction records and returns them.
    """
    return (
        db.query(Transaction)
        .order_by(Transaction.timestamp.desc())
        .all()
    )

def get_transaction_by_id(db: Session, transaction_id: int):
    """
    Retrieve a single Transaction by its ID (returns None if not found).
    """
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()

def create_transaction_record(tx_data: dict, db: Session) -> Transaction:
    """
    Creates a new Transaction in the hybrid multi-line ledger system.

    Steps:
     1) Ensure "BTC Fees" account exists.
     2) Validate transaction type usage.
     3) Validate fee usage for transaction type.
     4) Create Transaction row in DB.
     5) Convert single-entry fields => multiple ledger lines.
     6) Possibly skip net-zero check if cross-currency (Buy/Sell).
     7) If Deposit/Buy => create BTC lot if to_acct=BTC
     8) If Withdrawal/Sell => do FIFO disposal if from_acct=BTC
     9) If disposal => compute realized gains summary
    """
    # Step 1
    ensure_fee_account_exists(db)

    # Step 2 & 3
    _enforce_transaction_type_rules(tx_data, db)
    _enforce_fee_rules(tx_data, db)

    # Step 4
    now_utc = datetime.now(timezone.utc)
    new_tx = Transaction(
        from_account_id=tx_data.get("from_account_id"),
        to_account_id=tx_data.get("to_account_id"),
        type=tx_data.get("type"),
        amount=tx_data.get("amount"),
        fee_amount=tx_data.get("fee_amount"),
        fee_currency=tx_data.get("fee_currency"),
        timestamp=tx_data.get("timestamp", now_utc),
        source=tx_data.get("source"),
        purpose=tx_data.get("purpose"),
        cost_basis_usd=tx_data.get("cost_basis_usd"),
        proceeds_usd=tx_data.get("proceeds_usd"),
        is_locked=tx_data.get("is_locked", False),
        created_at=now_utc,
        updated_at=now_utc
    )
    db.add(new_tx)
    db.flush()  # get new_tx.id

    # Optional grouping usage
    new_tx.group_id = new_tx.id

    # Step 5
    remove_ledger_entries_for_tx(new_tx, db)
    build_ledger_entries_for_transaction(new_tx, tx_data, db)

    # Step 6
    _maybe_verify_balance_for_internal(new_tx, db)

    # Steps 7-9: partial-lot logic
    if new_tx.type in ("Deposit", "Buy"):
        maybe_create_bitcoin_lot(new_tx, tx_data, db)
    elif new_tx.type in ("Withdrawal", "Sell"):
        maybe_dispose_lots_fifo(new_tx, tx_data, db)
        compute_sell_summary_from_disposals(new_tx, db)
    elif new_tx.type == "Transfer":
        from_acct = db.query(Account).filter(Account.id == new_tx.from_account_id).first()
        if from_acct and from_acct.currency == "BTC":
            if new_tx.fee_amount is None or new_tx.fee_amount <= 0:
                logging.warning(f"Transfer {new_tx.id} missing fee_amount; defaulting to 0")
                new_tx.fee_amount = Decimal("0")
            if not new_tx.fee_currency:
                new_tx.fee_currency = "BTC"
        maybe_transfer_bitcoin_lot(new_tx, tx_data, db)

    # If disposal => finalize realized gain summary
    if new_tx.type in ("Sell", "Withdrawal"):
        compute_sell_summary_from_disposals(new_tx, db)

    db.commit()
    db.refresh(new_tx)
    return new_tx

def update_transaction_record(transaction_id: int, tx_data: dict, db: Session):
    """
    Update an existing Transaction (if not locked).

    Steps:
     - If locked => return None
     - Re-validate usage & fee rules if relevant fields changed
     - Overwrite transaction fields
     - Rebuild ledger lines
     - Possibly skip net-zero if cross-currency (Buy/Sell)
     - Re-run partial-lot logic for each relevant type
     - If disposal => compute realized gain summary
     - "Scorched earth": recalculate ALL transactions in strict chronological order
     - (NEW) Compare old vs. new timestamp; if we backdate, we also illustrate partial-lot
       recalculation from earliest_of(old, new).
       *We still call recalculate_all_transactions(...) to preserve original logic.*
    """
    tx = get_transaction_by_id(db, transaction_id)
    if not tx or tx.is_locked:
        return None

    # Store old timestamp for backdate comparison
    old_timestamp = tx.timestamp

    # Re-validate usage & fee rules if certain fields changed
    if any(k in tx_data for k in ("type", "from_account_id", "to_account_id")):
        _enforce_transaction_type_rules(tx_data, db)
    if any(k in tx_data for k in ("fee_amount", "fee_currency", "type")):
        _enforce_fee_rules(tx_data, db)

    # Update fields
    if "from_account_id" in tx_data:
        tx.from_account_id = tx_data["from_account_id"]
    if "to_account_id" in tx_data:
        tx.to_account_id = tx_data["to_account_id"]
    if "amount" in tx_data:
        tx.amount = tx_data["amount"]
    if "fee_amount" in tx_data:
        tx.fee_amount = tx_data["fee_amount"]
    if "fee_currency" in tx_data:
        tx.fee_currency = tx_data["fee_currency"]
    if "type" in tx_data:
        tx.type = tx_data["type"]
    if "timestamp" in tx_data:
        tx.timestamp = tx_data["timestamp"]
    if "source" in tx_data:
        tx.source = tx_data["source"]
    if "purpose" in tx_data:
        tx.purpose = tx_data["purpose"]
    if "cost_basis_usd" in tx_data:
        tx.cost_basis_usd = tx_data["cost_basis_usd"]
    if "proceeds_usd" in tx_data:
        tx.proceeds_usd = tx_data["proceeds_usd"]

    tx.updated_at = datetime.now(timezone.utc)

    # Remove ledger entries & partial-lot usage for this tx
    remove_ledger_entries_for_tx(tx, db)
    remove_lot_usage_for_tx(tx, db)

    # Rebuild ledger lines
    build_ledger_entries_for_transaction(tx, tx_data, db)
    _maybe_verify_balance_for_internal(tx, db)

    # Partial-lot logic
    if tx.type in ("Deposit", "Buy"):
        maybe_create_bitcoin_lot(tx, tx_data, db)
    elif tx.type == "Transfer":
        maybe_transfer_bitcoin_lot(tx, tx_data, db)
    elif tx.type in ("Sell", "Withdrawal"):
        maybe_dispose_lots_fifo(tx, tx_data, db)
        compute_sell_summary_from_disposals(tx, db)

    # -------------------------------------------------------------------------
    # Step 7 addition: Compare old vs. new timestamps to detect backdating
    # -------------------------------------------------------------------------
    new_timestamp = tx.timestamp
    earliest_timestamp = min(old_timestamp, new_timestamp)
    if new_timestamp < old_timestamp:
        # We are explicitly backdating, so let's illustrate partial-lot re-lot
        logging.info(
            f"[Backdating Detected] Transaction {tx.id} moved from {old_timestamp} "
            f"to {new_timestamp}. Re-lot from earliest={earliest_timestamp}"
        )
        recalculate_subsequent_transactions(db, earliest_timestamp)
    else:
        # If it's not backdated, you could still partial-lot re-lot if you want:
        logging.info(
            f"[Timestamp Forward/Unchanged] Transaction {tx.id} moved from {old_timestamp} "
            f"to {new_timestamp}. (No partial-lot re-lot needed unless desired.)"
        )

    # -------------------------------------------------------------------------
    # Preserve old "scorched earth" approach:
    # -------------------------------------------------------------------------
    recalculate_all_transactions(db)
    # -------------------------------------------------------------------------

    db.commit()
    db.refresh(tx)
    return tx

def delete_transaction_record(transaction_id: int, db: Session):
    """
    Delete a transaction if not locked. Removes ledger entries,
    lots, disposals referencing it, then re-lots everything.
    """
    tx = get_transaction_by_id(db, transaction_id)
    if not tx or tx.is_locked:
        return False

    # 1) Delete the transaction itself
    db.delete(tx)
    db.commit()

    # 2) Re-lot *all* transactions from scratch
    recalculate_all_transactions(db)

    return True

# --------------------------------------------------------------------------------
# Internal Helpers
# --------------------------------------------------------------------------------

def ensure_fee_account_exists(db: Session):
    """
    If a 'BTC Fees' account doesn't exist, create it.
    Allows any fee ledger line referencing 'BTC Fees' to avoid FK issues.
    """
    fee_acct = db.query(Account).filter_by(name="BTC Fees").first()
    if not fee_acct:
        fee_acct = Account(
            user_id=1,
            name="BTC Fees",
            currency="BTC"
        )
        db.add(fee_acct)
        db.commit()
        db.refresh(fee_acct)
    return fee_acct

def remove_ledger_entries_for_tx(tx: Transaction, db: Session):
    """
    Remove all LedgerEntry lines for this transaction.
    """
    for entry in list(tx.ledger_entries):
        db.delete(entry)
    db.flush()

def remove_lot_usage_for_tx(tx: Transaction, db: Session):
    """
    Remove any partial-lot disposals or newly created lots for this transaction.
    """
    for disp in list(tx.lot_disposals):
        db.delete(disp)
    for lot in list(tx.bitcoin_lots_created):
        db.delete(lot)
    db.flush()

def build_ledger_entries_for_transaction(tx: Transaction, tx_data: dict, db: Session):
    """
    Convert single-entry fields => multi-line ledger.
    Subtract the fee from proceeds in a Sell, so net is credited to 'to_acct'.
    """
    from_acct_id = tx_data.get("from_account_id")
    to_acct_id = tx_data.get("to_account_id")
    tx_type = tx_data.get("type", "")
    amount = Decimal(tx_data.get("amount", 0))
    fee_amount = Decimal(tx_data.get("fee_amount", 0))
    fee_currency = (tx_data.get("fee_currency") or "BTC").upper()

    proceeds_str = tx_data.get("proceeds_usd", "0")
    proceeds_usd = Decimal(proceeds_str) if proceeds_str else Decimal("0")

    from_acct = db.query(Account).filter(Account.id == from_acct_id).first() if from_acct_id else None
    to_acct = db.query(Account).filter(Account.id == to_acct_id).first() if to_acct_id else None

    # Transfer with BTC fee
    if (
        tx_type == "Transfer"
        and from_acct
        and from_acct.currency == "BTC"
        and fee_amount > 0
    ):
        db.add(LedgerEntry(
            transaction_id=tx.id,
            account_id=from_acct.id,
            amount=-amount,
            currency=from_acct.currency,
            entry_type="MAIN_OUT"
        ))
        if to_acct and amount > 0:
            net_in = amount - fee_amount
            db.add(LedgerEntry(
                transaction_id=tx.id,
                account_id=to_acct.id,
                amount=net_in if net_in > 0 else Decimal(0),
                currency=to_acct.currency,
                entry_type="MAIN_IN"
            ))
        fee_acct = db.query(Account).filter_by(name="BTC Fees").first()
        if fee_acct:
            db.add(LedgerEntry(
                transaction_id=tx.id,
                account_id=fee_acct.id,
                amount=fee_amount,
                currency="BTC",
                entry_type="FEE"
            ))
        db.flush()
        return

    # Sell => from BTC to USD
    if (
        tx_type == "Sell"
        and from_acct and from_acct.currency == "BTC"
        and to_acct and to_acct.currency == "USD"
    ):
        # Subtract BTC
        if amount > 0:
            db.add(LedgerEntry(
                transaction_id=tx.id,
                account_id=from_acct.id,
                amount=-amount,
                currency="BTC",
                entry_type="MAIN_OUT"
            ))
        net_usd_in = proceeds_usd
        if fee_currency == "USD":
            net_usd_in = proceeds_usd - fee_amount
            if net_usd_in < 0:
                net_usd_in = Decimal("0")

        # Overwrite with new net proceeds
        tx_data["proceeds_usd"] = str(net_usd_in)

        # Add USD in
        if net_usd_in > 0:
            db.add(LedgerEntry(
                transaction_id=tx.id,
                account_id=to_acct.id,
                amount=net_usd_in,
                currency="USD",
                entry_type="MAIN_IN"
            ))
        # Fee line to "USD Fees"
        if fee_amount > 0 and fee_currency == "USD":
            fee_acct = db.query(Account).filter_by(name="USD Fees").first()
            if fee_acct:
                db.add(LedgerEntry(
                    transaction_id=tx.id,
                    account_id=fee_acct.id,
                    amount=fee_amount,
                    currency="USD",
                    entry_type="FEE"
                ))
        db.flush()
        return

    # Buy => from USD to BTC
    if (
        tx_type == "Buy"
        and from_acct
        and from_acct.currency == "USD"
        and to_acct
        and to_acct.currency == "BTC"
    ):
        amount_btc = Decimal(tx_data.get("amount", "0"))
        fee_amt = Decimal(tx_data.get("fee_amount", "0"))
        cost_basis_usd = Decimal(tx_data.get("cost_basis_usd", "0"))

        total_usd_out = cost_basis_usd + fee_amt

        db.add(LedgerEntry(
            transaction_id=tx.id,
            account_id=from_acct.id,
            amount=-total_usd_out,
            currency="USD",
            entry_type="MAIN_OUT"
        ))
        if amount_btc > 0:
            db.add(LedgerEntry(
                transaction_id=tx.id,
                account_id=to_acct.id,
                amount=amount_btc,
                currency="BTC",
                entry_type="MAIN_IN"
            ))
        if fee_amt > 0 and fee_currency == "USD":
            fee_acct = db.query(Account).filter_by(name="USD Fees").first()
            if fee_acct:
                db.add(LedgerEntry(
                    transaction_id=tx.id,
                    account_id=fee_acct.id,
                    amount=fee_amt,
                    currency="USD",
                    entry_type="FEE"
                ))
        db.flush()
        return

    # Fallback: deposits, withdrawals, or any other type
    if from_acct and amount > 0:
        main_out_amt = -(amount + fee_amount)
        db.add(LedgerEntry(
            transaction_id=tx.id,
            account_id=from_acct.id,
            amount=main_out_amt,
            currency=from_acct.currency,
            entry_type="MAIN_OUT"
        ))
    if to_acct and amount > 0:
        db.add(LedgerEntry(
            transaction_id=tx.id,
            account_id=to_acct.id,
            amount=amount,
            currency=to_acct.currency,
            entry_type="MAIN_IN"
        ))
    if fee_amount > 0:
        if fee_currency == "BTC":
            fee_acct = db.query(Account).filter_by(name="BTC Fees").first()
        else:
            fee_acct = db.query(Account).filter_by(name="USD Fees").first()
        if fee_acct:
            db.add(LedgerEntry(
                transaction_id=tx.id,
                account_id=fee_acct.id,
                amount=fee_amount,
                currency=fee_currency,
                entry_type="FEE"
            ))
    db.flush()

def maybe_create_bitcoin_lot(tx: Transaction, tx_data: dict, db: Session):
    """
    If Deposit/Buy => create a BitcoinLot if to_acct=BTC.
    cost_basis_usd is used to track how many USD were effectively spent.
    If fee is USD for a Buy, add it to cost basis automatically.
    """
    to_acct = db.query(Account).filter(Account.id == tx.to_account_id).first()
    if not to_acct or to_acct.currency != "BTC":
        return

    btc_amount = tx.amount or Decimal("0")
    if btc_amount <= 0:
        return

    cost_basis = Decimal(tx_data.get("cost_basis_usd", "0"))
    fee_cur = (tx_data.get("fee_currency") or "").upper()
    fee_amt = Decimal(tx_data.get("fee_amount", "0"))

    # If it's a Buy w/ USD fee, add that fee to cost basis
    if tx.type == "Buy" and fee_cur == "USD":
        cost_basis += fee_amt

    new_lot = BitcoinLot(
        created_txn_id=tx.id,
        acquired_date=tx.timestamp,
        total_btc=btc_amount,
        remaining_btc=btc_amount,
        cost_basis_usd=cost_basis,
    )
    db.add(new_lot)
    db.flush()

def maybe_dispose_lots_fifo(tx: Transaction, tx_data: dict, db: Session):
    """
    For a Sell or Withdrawal from a BTC account, dispose BTC in FIFO order.
    Creates partial-lot disposal records, each with a holding_period based on
    (tx.timestamp - lot.acquired_date).days

    Additional Handling for Withdrawals:
     - If purpose=Gift/Donation/Lost => proceeds=0 (forced)
     - If purpose=Spent => we allow user-supplied 'proceeds_usd' (like a pseudo-sell),
       then subtract BTC fee from net proceeds if fee is BTC.
     - Otherwise, if 'proceeds_usd' is missing, default to 0.
    """

    from_acct = db.query(Account).filter(Account.id == tx.from_account_id).first()
    if not from_acct or from_acct.currency != "BTC":
        return  # Only dispose if withdrawing BTC

    btc_outflow = float(tx.amount or 0)
    if btc_outflow <= 0:
        return

    # 1) Handle proceeds_usd carefully (default to 0 if None)
    raw_proceeds = tx_data.get("proceeds_usd")
    if raw_proceeds is None:
        raw_proceeds = "0"
    try:
        total_proceeds = float(raw_proceeds)
    except ValueError:
        # If someone passed something non-numeric, default to 0
        total_proceeds = 0.0

    withdrawal_purpose = (tx.purpose or "").strip()
    
    # 2) If Gift/Donation/Lost => forced 0 proceeds
    if tx.type == "Withdrawal" and withdrawal_purpose in ("Gift", "Donation", "Lost"):
        total_proceeds = 0.0

    # 3) If "Spent" => reduce net proceeds by BTC fee if any
    if tx.type == "Withdrawal" and withdrawal_purpose == "Spent":
        fee_btc = float(tx.fee_amount or 0)
        fee_cur = (tx.fee_currency or "").upper()
        # If there's a BTC fee and we have some total_proceeds (like a pseudo-sell),
        # we recalculate net_proceeds after paying the fee in BTC.
        if fee_btc > 0 and fee_cur == "BTC" and btc_outflow > 0 and total_proceeds > 0:
            implied_price = total_proceeds / btc_outflow
            fee_in_usd = fee_btc * implied_price
            net_proceeds = total_proceeds - fee_in_usd
            if net_proceeds < 0:
                net_proceeds = 0.0
            total_proceeds = net_proceeds

    # 4) Continue with your existing FIFO disposal logic
    lots = (
        db.query(BitcoinLot)
        .filter(BitcoinLot.remaining_btc > 0)
        .order_by(BitcoinLot.acquired_date)
        .all()
    )
    remaining_outflow = btc_outflow
    total_outflow = btc_outflow

    for lot in lots:
        if remaining_outflow <= 0:
            break
        lot_rem = float(lot.remaining_btc)
        if lot_rem <= 0:
            continue

        can_use = min(lot_rem, remaining_outflow)
        original_cost_per_btc = Decimal(lot.cost_basis_usd) / Decimal(lot.total_btc)
        disposal_basis = (original_cost_per_btc * Decimal(can_use)).quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)

        # Calculate partial proceeds proportionally
        partial_proceeds = Decimal("0.0")
        if total_outflow > 0:
            ratio = Decimal(can_use) / Decimal(total_outflow)
            partial_proceeds = (ratio * Decimal(total_proceeds)).quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)

        # If Gift/Donation/Lost => we already forced total_proceeds=0.0,
        # so partial_proceeds is 0 anyway, meaning disposal_gain => 0
        disposal_gain = partial_proceeds - disposal_basis
        if tx.type == "Withdrawal" and withdrawal_purpose in ("Gift", "Donation", "Lost"):
            disposal_gain = Decimal("0.0")

        # Ensure acquired_date is UTC
        acquired_date = lot.acquired_date
        if acquired_date.tzinfo is None:
            acquired_date = acquired_date.replace(tzinfo=timezone.utc)

        days_held = (tx.timestamp - acquired_date).days
        hp = "LONG" if days_held >= 365 else "SHORT"

        disp = LotDisposal(
            lot_id=lot.id,
            transaction_id=tx.id,
            disposed_btc=Decimal(can_use),
            disposal_basis_usd=disposal_basis,
            proceeds_usd_for_that_portion=partial_proceeds,
            realized_gain_usd=disposal_gain,
            holding_period=hp
        )
        db.add(disp)

        lot.remaining_btc = Decimal(lot_rem - can_use)
        remaining_outflow -= can_use

    db.flush()

def compute_sell_summary_from_disposals(tx: Transaction, db: Session):
    """
    Summarize partial-lot disposals for a Sell/Withdrawal. Overwrite
    tx.cost_basis_usd, tx.proceeds_usd, tx.realized_gain_usd, holding_period
    based on the earliest acquisition date among those partial-lot disposals.
    """
    disposals = db.query(LotDisposal).filter(LotDisposal.transaction_id == tx.id).all()
    if not disposals:
        return

    total_basis = Decimal("0.0")
    total_gain = Decimal("0.0")
    total_proceeds = Decimal("0.0")
    earliest_date = None

    for disp in disposals:
        total_basis += (disp.disposal_basis_usd or Decimal("0"))
        total_gain += (disp.realized_gain_usd or Decimal("0"))
        total_proceeds += (disp.proceeds_usd_for_that_portion or Decimal("0"))

        lot = db.query(BitcoinLot).get(disp.lot_id)
        if lot and (earliest_date is None or lot.acquired_date < earliest_date):
            earliest_date = lot.acquired_date

    tx.cost_basis_usd = total_basis
    tx.realized_gain_usd = total_gain

    # Only overwrite proceeds if partial-lot proceeds > 0
    if total_proceeds > 0:
        tx.proceeds_usd = total_proceeds

    if earliest_date:
        if earliest_date.tzinfo is None:
            earliest_date = earliest_date.replace(tzinfo=timezone.utc)
        days_held = (tx.timestamp - earliest_date).days
        tx.holding_period = "LONG" if days_held >= 365 else "SHORT"
    else:
        tx.holding_period = None

    db.flush()

def get_btc_price(timestamp: datetime, db: Session) -> Decimal:
    """
    Fetch the historical BTC price in USD at the given timestamp using /api/bitcoin/price/history.
    Falls back to live price if historical fails.
    """
    try:
        timestamp_str = timestamp.strftime("%Y-%m-%d")
        response = requests.get(
            "http://localhost:8000/api/bitcoin/price/history",
            params={"date": timestamp_str}
        )
        response.raise_for_status()
        price_data = response.json()
        if "USD" not in price_data:
            raise ValueError("USD price not found in response")
        return Decimal(str(price_data["USD"]))
    except (requests.RequestException, ValueError, KeyError) as e:
        # Attempt fallback to live
        try:
            live_resp = requests.get("http://localhost:8000/api/bitcoin/price")
            live_resp.raise_for_status()
            live_price_data = live_resp.json()
            if "USD" in live_price_data:
                return Decimal(str(live_price_data["USD"]))
        except (requests.RequestException, ValueError, KeyError):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch BTC price: {str(e)}"
            )

def maybe_transfer_bitcoin_lot(tx: Transaction, tx_data: dict, db: Session):
    """
    Splits source lots when transferring BTC internally between two BTC accounts.
     - Main transferred portion is *not* a disposal
     - Fee portion is a disposal
     - Create new partial-lot(s) in the destination for the remainder

    Steps:
      1) total_outflow = (transfer amount + fee)
      2) gather lots (FIFO)
      3) partial-lot disposal for fee, new partial-lot for remainder
      4) set holding_period=SHORT/LONG for the fee disposal
    """
    from_acct = db.query(Account).filter(Account.id == tx.from_account_id).first()
    to_acct = db.query(Account).filter(Account.id == tx.to_account_id).first()
    if not from_acct or not to_acct:
        return
    if from_acct.currency != "BTC" or to_acct.currency != "BTC":
        return

    btc_outflow = Decimal(tx.amount or 0)
    fee_btc = Decimal(tx.fee_amount or 0) if (tx.fee_currency or "").upper() == "BTC" else Decimal("0")
    total_outflow = btc_outflow + fee_btc
    if total_outflow <= 0:
        return

    # Gather all lots from 'from_acct' in FIFO
    lots = (
        db.query(BitcoinLot)
        .join(Transaction, Transaction.id == BitcoinLot.created_txn_id)
        .filter(
            BitcoinLot.remaining_btc > 0,
            Transaction.to_account_id == tx.from_account_id
        )
        .order_by(BitcoinLot.acquired_date.asc())
        .all()
    )

    remaining_outflow = total_outflow
    remaining_fee = fee_btc
    transfers_for_destination = []

    for lot in lots:
        if remaining_outflow <= 0:
            break
        if lot.remaining_btc <= 0:
            continue

        btc_to_use = min(lot.remaining_btc, remaining_outflow)
        if lot.total_btc > 0:
            cost_per_btc = lot.cost_basis_usd / lot.total_btc
        else:
            cost_per_btc = Decimal("0")
        cost_portion = (cost_per_btc * btc_to_use).quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)

        lot.remaining_btc = lot.remaining_btc - Decimal(btc_to_use)
        db.add(lot)
        remaining_outflow -= btc_to_use

        portion_for_fee = min(btc_to_use, remaining_fee)
        portion_for_dest = btc_to_use - portion_for_fee

        # Fee disposal
        if portion_for_fee > 0:
            disposal_basis = (cost_per_btc * portion_for_fee).quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)
            btc_unit_price = get_btc_price(tx.timestamp, db)
            proceeds_for_fee = (btc_unit_price * portion_for_fee).quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)
            realized_gain = proceeds_for_fee - disposal_basis

            acquired_date = lot.acquired_date
            if acquired_date.tzinfo is None:
                acquired_date = acquired_date.replace(tzinfo=timezone.utc)
            days_held = (tx.timestamp - acquired_date).days
            hp = "LONG" if days_held >= 365 else "SHORT"

            disp = LotDisposal(
                lot_id=lot.id,
                transaction_id=tx.id,
                disposed_btc=Decimal(portion_for_fee),
                disposal_basis_usd=disposal_basis,
                proceeds_usd_for_that_portion=proceeds_for_fee,
                realized_gain_usd=realized_gain,
                holding_period=hp
            )
            db.add(disp)
            remaining_fee -= portion_for_fee

        # Destination partial-lot
        if portion_for_dest > 0:
            transfers_for_destination.append((lot, portion_for_dest, cost_per_btc, lot.acquired_date))

    # If not enough BTC to cover fee or total outflow, raise error
    if remaining_fee > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough BTC to cover fee {fee_btc}"
        )
    if remaining_outflow > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough BTC to transfer {btc_outflow} + fee {fee_btc}"
        )

    # Create new partial-lot(s) for destination
    for (orig_lot, amt_btc, cost_per_btc, acquired_date) in transfers_for_destination:
        if acquired_date.tzinfo is None:
            acquired_date = acquired_date.replace(tzinfo=timezone.utc)
        cost_portion = (cost_per_btc * amt_btc).quantize(Decimal("0.01"), rounding=ROUND_HALF_DOWN)
        new_lot = BitcoinLot(
            created_txn_id=tx.id,
            acquired_date=acquired_date,
            total_btc=Decimal(amt_btc),
            remaining_btc=Decimal(amt_btc),
            cost_basis_usd=cost_portion
        )
        db.add(new_lot)

    db.flush()

def recalculate_all_transactions(db: Session):
    """
    "Scorched Earth" Re-lot Approach:
     1) Remove ALL ledger entries, lot disposals, and Bitcoin lots
     2) Fetch every transaction in ascending order (timestamp, id)
     3) Re-build ledger lines & partial-lot logic for each transaction
    """
    db.query(LedgerEntry).delete()
    db.query(LotDisposal).delete()
    db.query(BitcoinLot).delete()
    db.flush()

    all_txs = (
        db.query(Transaction)
        .order_by(Transaction.timestamp.asc(), Transaction.id.asc())
        .all()
    )

    for rec_tx in all_txs:
        sub_tx_data = {
            "from_account_id": rec_tx.from_account_id,
            "to_account_id": rec_tx.to_account_id,
            "type": rec_tx.type,
            "amount": rec_tx.amount,
            "fee_amount": rec_tx.fee_amount,
            "fee_currency": rec_tx.fee_currency,
            "cost_basis_usd": rec_tx.cost_basis_usd,
            "proceeds_usd": rec_tx.proceeds_usd,
            "timestamp": rec_tx.timestamp,
            "source": rec_tx.source,
            "purpose": rec_tx.purpose,
        }
        build_ledger_entries_for_transaction(rec_tx, sub_tx_data, db)
        _maybe_verify_balance_for_internal(rec_tx, db)

        if rec_tx.type in ("Deposit", "Buy"):
            maybe_create_bitcoin_lot(rec_tx, sub_tx_data, db)
        elif rec_tx.type in ("Sell", "Withdrawal"):
            maybe_dispose_lots_fifo(rec_tx, sub_tx_data, db)
            compute_sell_summary_from_disposals(rec_tx, db)
        elif rec_tx.type == "Transfer":
            maybe_transfer_bitcoin_lot(rec_tx, sub_tx_data, db)

    db.flush()

# ------------------------------------------------------------------------------
# (NEW) PARTIAL REALLOCATION FUNCTION FOR STEP 7 BACKDATING
# ------------------------------------------------------------------------------
def recalculate_subsequent_transactions(db: Session, from_timestamp: datetime):
    """
    Example partial-lot re-lot approach from Step 7:
     - Only re-lot transactions whose timestamp >= from_timestamp.
     - This can be more efficient than "scorched earth" for large datasets.
     - We preserve recalculate_all_transactions(...) for completeness.
    """
    logging.info(
        f"[Partial Re-Lot] Starting from timestamp={from_timestamp.isoformat()}"
    )

    # 1) Gather all transactions from that timestamp forward
    affected_txs = (
        db.query(Transaction)
        .filter(Transaction.timestamp >= from_timestamp)
        .order_by(Transaction.timestamp.asc(), Transaction.id.asc())
        .all()
    )

    # 2) Remove ledger entries, disposals, lots only for these affected transactions
    #    so we can re-lot them in correct chronological order
    tx_ids = [t.id for t in affected_txs]
    db.query(LedgerEntry).filter(LedgerEntry.transaction_id.in_(tx_ids)).delete(synchronize_session=False)
    db.query(LotDisposal).filter(LotDisposal.transaction_id.in_(tx_ids)).delete(synchronize_session=False)
    db.query(BitcoinLot).filter(BitcoinLot.created_txn_id.in_(tx_ids)).delete(synchronize_session=False)
    db.flush()

    # 3) Rebuild each transaction’s ledger and partial-lot usage
    for rec_tx in affected_txs:
        sub_tx_data = {
            "from_account_id": rec_tx.from_account_id,
            "to_account_id": rec_tx.to_account_id,
            "type": rec_tx.type,
            "amount": rec_tx.amount,
            "fee_amount": rec_tx.fee_amount,
            "fee_currency": rec_tx.fee_currency,
            "cost_basis_usd": rec_tx.cost_basis_usd,
            "proceeds_usd": rec_tx.proceeds_usd,
            "timestamp": rec_tx.timestamp,
            "source": rec_tx.source,
            "purpose": rec_tx.purpose,
        }
        build_ledger_entries_for_transaction(rec_tx, sub_tx_data, db)
        _maybe_verify_balance_for_internal(rec_tx, db)

        if rec_tx.type in ("Deposit", "Buy"):
            maybe_create_bitcoin_lot(rec_tx, sub_tx_data, db)
        elif rec_tx.type in ("Sell", "Withdrawal"):
            maybe_dispose_lots_fifo(rec_tx, sub_tx_data, db)
            compute_sell_summary_from_disposals(rec_tx, db)
        elif rec_tx.type == "Transfer":
            maybe_transfer_bitcoin_lot(rec_tx, sub_tx_data, db)

    db.flush()
    logging.info("[Partial Re-Lot] Completed partial-lot recalculation.")

# --------------------------------------------------------------------------------
# Double-Entry (with Cross-Currency Skip) & Fee Rules
# --------------------------------------------------------------------------------

def _maybe_verify_balance_for_internal(tx: Transaction, db: Session):
    """
    If type=Buy or Sell => skip net-zero check; cross-currency doesn't net to zero.
    Otherwise, for internal accounts, enforce net=0 by currency (except external=99).
    """
    if tx.type in ("Buy", "Sell"):
        return
    _verify_double_entry_balance_for_internal(tx, db)

def _verify_double_entry_balance_for_internal(tx: Transaction, db: Session):
    """
    Ensure ledger entries net to zero by currency for internal transactions
    (i.e., from_acct != 99, to_acct != 99).
    """
    if tx.from_account_id == 99 or tx.to_account_id == 99:
        return

    ledger_entries = db.query(LedgerEntry).filter(LedgerEntry.transaction_id == tx.id).all()
    sums_by_currency = defaultdict(Decimal)
    for entry in ledger_entries:
        if entry.account_id != 99:
            sums_by_currency[entry.currency] += entry.amount

    for currency, total in sums_by_currency.items():
        if total != Decimal("0"):
            raise HTTPException(
                status_code=400,
                detail=f"Ledger not balanced for {currency}: {total}"
            )

def _enforce_fee_rules(tx_data: dict, db: Session):
    """
    Validate fee usage by transaction type:
      - Transfer => fee must match from_acct currency
      - Buy/Sell => fee must be USD
      - Deposit/Withdrawal => no special fee rule
    """
    tx_type = tx_data.get("type")
    from_id = tx_data.get("from_account_id")
    fee_amount = Decimal(tx_data.get("fee_amount", 0))
    fee_currency = (tx_data.get("fee_currency") or "USD").upper()

    if fee_amount <= 0:
        return

    if tx_type == "Transfer":
        if not from_id or from_id == 99:
            return
        from_acct = db.query(Account).filter(Account.id == from_id).first()
        if from_acct and from_acct.currency == "BTC" and fee_currency != "BTC":
            raise HTTPException(
                status_code=400,
                detail="Transfer from BTC => fee must be BTC."
            )
        if from_acct and from_acct.currency == "USD" and fee_currency != "USD":
            raise HTTPException(
                status_code=400,
                detail="Transfer from USD => fee must be USD."
            )
    elif tx_type in ("Buy", "Sell"):
        if fee_currency != "USD":
            raise HTTPException(
                status_code=400,
                detail=f"{tx_type} => fee must be USD."
            )

def _enforce_transaction_type_rules(tx_data: dict, db: Session):
    """
    Enforce correct usage:
      - Deposit => from=99 => to=internal
      - Withdrawal => from=internal => to=99
      - Transfer => both from/to internal & same currency
      - Buy => from=3 => to=4
      - Sell => from=4 => to=3
    """
    tx_type = tx_data.get("type")
    from_id = tx_data.get("from_account_id")
    to_id   = tx_data.get("to_account_id")

    if tx_type == "Deposit":
        if from_id != 99:
            raise HTTPException(status_code=400, detail="Deposit => from=99 (external).")
        if not to_id or to_id == 99:
            raise HTTPException(status_code=400, detail="Deposit => to=internal account.")

    elif tx_type == "Withdrawal":
        if to_id != 99:
            raise HTTPException(status_code=400, detail="Withdrawal => to=99 (external).")
        if not from_id or from_id == 99:
            raise HTTPException(status_code=400, detail="Withdrawal => from=internal.")

    elif tx_type == "Transfer":
        if not from_id or from_id == 99 or not to_id or to_id == 99:
            raise HTTPException(status_code=400, detail="Transfer => both from/to must be internal.")
        db_from = db.query(Account).get(from_id)
        db_to = db.query(Account).get(to_id)
        if db_from and db_to and db_from.currency != db_to.currency:
            raise HTTPException(status_code=400, detail="Transfer => same currency required.")

    elif tx_type == "Buy":
        if from_id != 3:
            raise HTTPException(status_code=400, detail="Buy => from=3 (Exchange USD).")
        if to_id != 4:
            raise HTTPException(status_code=400, detail="Buy => to=4 (Exchange BTC).")

    elif tx_type == "Sell":
        if from_id != 4:
            raise HTTPException(status_code=400, detail="Sell => from=4 (Exchange BTC).")
        if to_id != 3:
            raise HTTPException(status_code=400, detail="Sell => to=3 (Exchange USD).")

    else:
        raise HTTPException(status_code=400, detail=f"Unknown transaction type: {tx_type}")

def delete_all_transactions(db: Session) -> int:
    """
    Bulk cleanup: Delete all transactions (and cascading references).
    Return the number of deleted transactions.
    """
    transactions = db.query(Transaction).all()
    count = len(transactions)
    for tx in transactions:
        db.delete(tx)
    db.commit()
    return count
