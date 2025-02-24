"""
backend/services/transaction.py

Core logic for BitcoinTX with a hybrid double-entry:
 - Single-Entry inputs (type, amount, from_account, to_account, etc.)
 - Multi-line LedgerEntry creation for same-currency double-entry
 - Cross-currency Buy/Sell skip net-zero checks to allow a simpler personal ledger
 - BTC FIFO logic for sells/withdrawals

Final Version Tailored for Hybrid BitcoinTX:
 - Deposits/Withdrawals: one-sided if external=99
 - Transfer: net-zero required if same currency
 - Buy/Sell: from=3->4 or 4->3, skip net-zero to avoid cross-currency mismatch
 - Fee rules: Buy/Sell => fee=USD, Transfer => fee matches from_acct currency
"""

from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal

from backend.models.transaction import (
    Transaction, LedgerEntry, BitcoinLot, LotDisposal
)
from backend.models.account import Account
from backend.schemas.transaction import TransactionCreate

from collections import defaultdict
from fastapi import HTTPException

# --------------------------------------------------------------------------------
# Public Functions
# --------------------------------------------------------------------------------

def get_all_transactions(db: Session):
    """
    Return all Transactions, typically ordered descending by timestamp.
    """
    return (
        db.query(Transaction)
        .order_by(Transaction.timestamp.desc())
        .all()
    )

def get_transaction_by_id(transaction_id: int, db: Session):
    """
    Retrieve a single Transaction by its ID, or None if not found.
    """
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()

def create_transaction_record(tx_data: dict, db: Session) -> Transaction:
    """
    Creates a new Transaction in the hybrid multi-line ledger system.

    1) Check/ensure "BTC Fees" account for fee ledger lines
    2) Validate transaction type usage (_enforce_transaction_type_rules)
    3) Validate fee rules by type (_enforce_fee_rules)
    4) Create Transaction row
    5) Convert single-entry fields => ledger lines
    6) Possibly skip net-zero if cross-currency (Buy/Sell)
    7) If Deposit/Buy => create BTC lot if to_acct=BTC
    8) If Withdrawal/Sell => do FIFO disposal if from_acct=BTC
    9) If Sell => compute realized gains from partial-lot disposal
    """
    ensure_fee_account_exists(db)
    _enforce_transaction_type_rules(tx_data, db)
    _enforce_fee_rules(tx_data, db)

    new_tx = Transaction(
        from_account_id = tx_data.get("from_account_id"),
        to_account_id   = tx_data.get("to_account_id"),
        type            = tx_data.get("type"),
        amount          = tx_data.get("amount"),
        fee_amount      = tx_data.get("fee_amount"),
        fee_currency    = tx_data.get("fee_currency"),
        timestamp       = tx_data.get("timestamp", datetime.utcnow()),
        source          = tx_data.get("source"),
        purpose         = tx_data.get("purpose"),
        cost_basis_usd  = tx_data.get("cost_basis_usd"),
        proceeds_usd    = tx_data.get("proceeds_usd"),
        is_locked       = tx_data.get("is_locked", False),
        created_at      = datetime.utcnow(),
        updated_at      = datetime.utcnow()
    )
    db.add(new_tx)
    db.flush()  # get new_tx.id
    # group_id is used in your system for grouping related transactions; we set it to the same as id
    new_tx.group_id = new_tx.id

    # First, remove any existing ledger entries to avoid duplicates on re-build
    remove_ledger_entries_for_tx(new_tx, db)
    # Build ledger entries (double-entry lines) from the single-entry fields
    build_ledger_entries_for_transaction(new_tx, tx_data, db)

    # Enforce net-zero if type != Buy/Sell (i.e. same-currency transfers must net to zero)
    _maybe_verify_balance_for_internal(new_tx, db)

    # If depositing or buying BTC, create a BitcoinLot
    if new_tx.type in ("Deposit", "Buy"):
        maybe_create_bitcoin_lot(new_tx, tx_data, db)

    # If withdrawing or selling BTC, do a FIFO disposal
    if new_tx.type in ("Withdrawal", "Sell"):
        maybe_dispose_lots_fifo(new_tx, tx_data, db)

    # If it's a Sell, compute aggregated cost basis / realized gain / holding period
    if new_tx.type == "Sell":
        compute_sell_summary_from_disposals(new_tx, db)

    db.commit()
    db.refresh(new_tx)
    return new_tx

def update_transaction_record(transaction_id: int, tx_data: dict, db: Session):
    """
    Update an existing Transaction (if not locked):
     - Re-validate usage/fee if type or from/to changed
     - Rebuild ledger lines
     - Possibly skip net-zero if cross-currency (Buy/Sell)
     - Re-create lots or disposal if changed from deposit->buy or amount changed
    """
    tx = get_transaction_by_id(transaction_id, db)
    if not tx or tx.is_locked:
        return None

    # re-validate usage & fee rules if relevant fields changed
    if any(k in tx_data for k in ("type","from_account_id","to_account_id")):
        _enforce_transaction_type_rules(tx_data, db)
    if any(k in tx_data for k in ("fee_amount","fee_currency","type")):
        _enforce_fee_rules(tx_data, db)

    # Overwrite header fields based on tx_data
    if "from_account_id" in tx_data:
        tx.from_account_id = tx_data["from_account_id"]
    if "to_account_id" in tx_data:
        tx.to_account_id   = tx_data["to_account_id"]
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

    tx.updated_at = datetime.utcnow()

    # Rebuild ledger lines from scratch (remove old lines, add new)
    remove_ledger_entries_for_tx(tx, db)
    remove_lot_usage_for_tx(tx, db)  # remove prior lot disposal or created lots if any
    build_ledger_entries_for_transaction(tx, tx_data, db)
    _maybe_verify_balance_for_internal(tx, db)

    # Re-run lot creation or disposal logic based on the updated type
    if tx.type in ("Deposit", "Buy"):
        maybe_create_bitcoin_lot(tx, tx_data, db)
    if tx.type in ("Withdrawal", "Sell"):
        maybe_dispose_lots_fifo(tx, tx_data, db)
        if tx.type == "Sell":
            compute_sell_summary_from_disposals(tx, db)

    db.commit()
    db.refresh(tx)
    return tx

def delete_transaction_record(transaction_id: int, db: Session):
    """
    Delete a transaction if not locked.
    Cascade removes ledger entries, lots, disposals.
    """
    tx = get_transaction_by_id(transaction_id, db)
    if not tx or tx.is_locked:
        return False

    db.delete(tx)
    db.commit()
    return True

# --------------------------------------------------------------------------------
# Internal Helpers
# --------------------------------------------------------------------------------

def ensure_fee_account_exists(db: Session):
    """
    If a 'BTC Fees' account doesn't exist, create it for
    storing fee lines on BTC-based transactions.
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
    Delete all existing ledger lines for this transaction
    so we can rebuild them if the user changes fields.
    """
    for entry in list(tx.ledger_entries):
        db.delete(entry)
    db.flush()

def remove_lot_usage_for_tx(tx: Transaction, db: Session):
    """
    Remove any BTC lots or partial-lot disposals
    previously created by this transaction.
    """
    for disp in list(tx.lot_disposals):
        db.delete(disp)
    for lot in list(tx.bitcoin_lots_created):
        db.delete(lot)
    db.flush()

def build_ledger_entries_for_transaction(tx: Transaction, tx_data: dict, db: Session):
    """
    Convert single-entry style fields => multi-line ledger:
      - MAIN_OUT => negative (amount + fee)
      - MAIN_IN => positive amount
      - FEE => fee line to 'BTC Fees' or same currency
    """
    from_acct_id = tx_data.get("from_account_id")
    to_acct_id   = tx_data.get("to_account_id")
    amount       = Decimal(tx_data.get("amount", 0))
    fee_amount   = Decimal(tx_data.get("fee_amount", 0))
    fee_curr     = tx_data.get("fee_currency", "BTC")

    from_acct = db.query(Account).filter(Account.id == from_acct_id).first() if from_acct_id else None
    to_acct   = db.query(Account).filter(Account.id == to_acct_id).first()   if to_acct_id else None

    # Outflow line from "from_acct"
    if from_acct and amount > 0:
        main_out_amt = -(amount + fee_amount)
        db.add(LedgerEntry(
            transaction_id=tx.id,
            account_id=from_acct.id,
            amount=main_out_amt,
            currency=from_acct.currency,
            entry_type="MAIN_OUT"
        ))

    # Inflow line to "to_acct"
    if to_acct and amount > 0:
        db.add(LedgerEntry(
            transaction_id=tx.id,
            account_id=to_acct.id,
            amount=amount,
            currency=to_acct.currency,
            entry_type="MAIN_IN"
        ))

    # Separate FEE line (goes to 'BTC Fees' account or could be same currency)
    if fee_amount > 0:
        fee_acct = db.query(Account).filter_by(name="BTC Fees").first()
        if fee_acct:
            db.add(LedgerEntry(
                transaction_id=tx.id,
                account_id=fee_acct.id,
                amount=fee_amount,
                currency=fee_curr,
                entry_type="FEE"
            ))

    db.flush()

def maybe_create_bitcoin_lot(tx: Transaction, tx_data: dict, db: Session):
    """
    If deposit/buy => we create a BitcoinLot if the 'to_acct' is BTC.
    (cost_basis_usd in 'tx_data' helps track how many USD we paid.)
    """
    to_acct = db.query(Account).filter(Account.id == tx.to_account_id).first()
    if not to_acct or to_acct.currency != "BTC":
        return

    btc_amount = tx.amount or Decimal(0)
    if btc_amount <= 0:
        return

    cost_basis = Decimal(tx_data.get("cost_basis_usd", 0))

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
    If withdrawal/sell => we do a FIFO partial-lot disposal if the 'from_acct' is BTC.
    This calculates partial cost basis for each lot used.

    REFRACTOR:
      - If (tx.type == "Withdrawal") and tx.purpose in ("Gift","Donation","Lost"),
        we skip recognized gain by setting disposal_gain=0. 
        Optionally, partial_proceeds can also be set to 0 for a non-taxable event.
    """
    from_acct = db.query(Account).filter(Account.id == tx.from_account_id).first()
    if not from_acct or from_acct.currency != "BTC":
        return

    # The outflow of BTC from this transaction
    btc_outflow = float(tx.amount or 0)
    if btc_outflow <= 0:
        return

    # Check if the user supplied proceeds for the disposal
    total_proceeds = float(tx_data.get("proceeds_usd", 0))

    # Retrieve all BTC lots that still have a remaining balance
    lots = db.query(BitcoinLot).filter(
        BitcoinLot.remaining_btc > 0
    ).order_by(BitcoinLot.acquired_date).all()

    remaining_outflow = btc_outflow
    total_outflow = btc_outflow

    # Grab the "purpose" from the transaction to see if it's Gift/Donation/Lost
    withdrawal_purpose = (tx.purpose or "").strip()

    for lot in lots:
        if remaining_outflow <= 0:
            break

        lot_rem = float(lot.remaining_btc)
        if lot_rem <= 0:
            continue

        # 'can_use' is how many BTC we dispose from the current lot
        can_use = min(lot_rem, remaining_outflow)

        # lot_fraction => the fraction of the total lot we're disposing
        # disposal_basis => fraction of the lot's cost basis
        lot_fraction = can_use / lot_rem
        disposal_basis = float(lot.cost_basis_usd) * lot_fraction

        # partial_proceeds => portion of total_proceeds allocated to this chunk
        partial_proceeds = 0.0
        if total_outflow > 0:
            partial_proceeds = (can_use / total_outflow) * total_proceeds

        # Normal recognized gain => (partial_proceeds - disposal_basis)
        disposal_gain = partial_proceeds - disposal_basis

        # -----------------------------------------------------------
        # NEW LOGIC: If user selected Gift/Donation/Lost => zero out gain
        # -----------------------------------------------------------
        if tx.type == "Withdrawal" and withdrawal_purpose in ("Gift", "Donation", "Lost"):
            disposal_gain = 0.0
            # Optionally: partial_proceeds = 0.0
            # so the user sees 0 proceeds for a non-taxable event
            # partial_proceeds = 0.0

        # Create a new LotDisposal record with final disposal values
        disp = LotDisposal(
            lot_id=lot.id,
            transaction_id=tx.id,
            disposed_btc=Decimal(can_use),
            disposal_basis_usd=Decimal(disposal_basis),
            proceeds_usd_for_that_portion=Decimal(partial_proceeds),
            realized_gain_usd=Decimal(disposal_gain)
        )
        db.add(disp)

        # Reduce the remaining BTC in the lot
        lot.remaining_btc = Decimal(lot_rem - can_use)

        # Decrement how much BTC we still need to dispose
        remaining_outflow -= can_use

    db.flush()

def compute_sell_summary_from_disposals(tx: Transaction, db: Session):
    """
    For a Sell => sum up the partial-lot disposals, set cost_basis_usd & realized_gain_usd,
    and determine holding_period = 'LONG' or 'SHORT'.
    """
    disposals = db.query(LotDisposal).filter(LotDisposal.transaction_id == tx.id).all()
    if not disposals:
        return

    total_basis = 0.0
    total_gain  = 0.0
    earliest_date = None

    for disp in disposals:
        total_basis += float(disp.disposal_basis_usd or 0)
        total_gain  += float(disp.realized_gain_usd or 0)

        lot = db.query(BitcoinLot).get(disp.lot_id)
        if lot and (earliest_date is None or lot.acquired_date < earliest_date):
            earliest_date = lot.acquired_date

    tx.cost_basis_usd    = Decimal(total_basis)
    tx.realized_gain_usd = Decimal(total_gain)

    # Check how many days between earliest_date of acquisition and the transaction date
    if earliest_date:
        days_held = (tx.timestamp.date() - earliest_date.date()).days
        tx.holding_period = "LONG" if days_held > 365 else "SHORT"
    else:
        tx.holding_period = None

    db.flush()

# --------------------------------------------------------------------------------
# Double-Entry (with Cross-Currency Skip) & Fee Rules
# --------------------------------------------------------------------------------

def _maybe_verify_balance_for_internal(tx: Transaction, db: Session):
    """
    If type=Buy or Sell => skip net-zero check, because cross-currency doesn't net to zero
    in our simplified approach.

    Otherwise we call _verify_double_entry_balance_for_internal for normal internal same-currency logic.
    """
    if tx.type in ("Buy", "Sell"):
        return
    _verify_double_entry_balance_for_internal(tx, db)

def _verify_double_entry_balance_for_internal(tx: Transaction, db: Session):
    """
    Only enforces net=0 if both from/to are internal (not 99).
    (If external=99 => skip, if cross-currency is Buy/Sell => we skip in the caller.)
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
    Transfer => fee matches from_acct currency
    Buy/Sell => fee must be USD
    (Deposit/Withdrawal => no special rule, can do any fee currency if wanted.)
    """
    tx_type = tx_data.get("type")
    from_id = tx_data.get("from_account_id")
    fee_amount = Decimal(tx_data.get("fee_amount", 0))
    fee_currency = tx_data.get("fee_currency", "USD")

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
    - Deposit => from=99, to internal
    - Withdrawal => from internal, to=99
    - Transfer => both internal same currency
    - Buy => from=3 => to=4
    - Sell => from=4 => to=3
    """
    tx_type = tx_data.get("type")
    from_id = tx_data.get("from_account_id")
    to_id   = tx_data.get("to_account_id")

    if tx_type == "Deposit":
        if from_id != 99:
            raise HTTPException(
                status_code=400,
                detail="Deposit => from=99 (external)."
            )
        if not to_id or to_id == 99:
            raise HTTPException(
                status_code=400,
                detail="Deposit => to=internal account."
            )

    elif tx_type == "Withdrawal":
        if to_id != 99:
            raise HTTPException(
                status_code=400,
                detail="Withdrawal => to=99 (external)."
            )
        if not from_id or from_id == 99:
            raise HTTPException(
                status_code=400,
                detail="Withdrawal => from=internal."
            )

    elif tx_type == "Transfer":
        if not from_id or from_id == 99 or not to_id or to_id == 99:
            raise HTTPException(
                status_code=400,
                detail="Transfer => both from/to must be internal."
            )
        # If we only allow same-currency transfers, verify that:
        db_from = db.query(Account).get(from_id)
        db_to   = db.query(Account).get(to_id)
        if db_from and db_to and db_from.currency != db_to.currency:
            raise HTTPException(
                status_code=400,
                detail="Transfer => from/to must share currency."
            )

    elif tx_type == "Buy":
        # Strict => from=3 => to=4
        if from_id != 3:
            raise HTTPException(
                status_code=400,
                detail="Buy => from=3 (Exchange USD)."
            )
        if to_id != 4:
            raise HTTPException(
                status_code=400,
                detail="Buy => to=4 (Exchange BTC)."
            )

    elif tx_type == "Sell":
        # Strict => from=4 => to=3
        if from_id != 4:
            raise HTTPException(
                status_code=400,
                detail="Sell => from=4 (Exchange BTC)."
            )
        if to_id != 3:
            raise HTTPException(
                status_code=400,
                detail="Sell => to=3 (Exchange USD)."
            )

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown transaction type: {tx_type}"
        )
    
def delete_all_transactions(db: Session) -> int:
    """
    Delete all transactions from the database and return the count of deleted transactions.
    """
    transactions = db.query(Transaction).all()
    count = len(transactions)
    for tx in transactions:
        db.delete(tx)
    db.commit()
    return count