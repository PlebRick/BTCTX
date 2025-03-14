# backend/services/transaction.py

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

Updates:
 - Sells: fee is subtracted from proceeds before disposal logic (so net proceeds are used).
 - Buys: fee is now automatically added to the cost basis in `maybe_create_bitcoin_lot`, 
   ensuring the user’s final lot has total = (typed cost + fee).
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

    1) Check/ensure "BTC Fees" account for fee ledger lines
    2) Validate transaction type usage (_enforce_transaction_type_rules)
    3) Validate fee rules by type (_enforce_fee_rules)
    4) Create Transaction row in DB
    5) Convert single-entry fields => multiple ledger lines (build_ledger_entries_for_transaction)
    6) Possibly skip net-zero check if cross-currency (Buy/Sell) (_maybe_verify_balance_for_internal)
    7) If Deposit/Buy => create BTC lot if to_acct=BTC (maybe_create_bitcoin_lot)
    8) If Withdrawal/Sell => do FIFO disposal if from_acct=BTC (maybe_dispose_lots_fifo)
    9) If it's a disposal (Withdrawal or Sell), compute realized gains summary (compute_sell_summary_from_disposals).
    """
    # Step 1: Ensure "BTC Fees" account exists (for storing fees in ledger)
    ensure_fee_account_exists(db)

    # Step 2: Validate transaction type usage
    _enforce_transaction_type_rules(tx_data, db)

    # Step 3: Validate fee rules by transaction type
    _enforce_fee_rules(tx_data, db)

    # Step 4: Create the Transaction row
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
    db.flush()  # get new_tx.id from DB

    # Optional group_id usage
    new_tx.group_id = new_tx.id

    # Step 5: Clear any old ledger lines (shouldn't be any for a new Tx) then rebuild
    remove_ledger_entries_for_tx(new_tx, db)
    build_ledger_entries_for_transaction(new_tx, tx_data, db)

   # Step 6: Possibly skip net-zero check if cross-currency (Buy/Sell)
    _maybe_verify_balance_for_internal(new_tx, db)

    # Steps 7-9: Handle lot creation, disposal, or transfer based on transaction type
    if new_tx.type in ("Deposit", "Buy"):
        # Step 7: If depositing or buying BTC, create a BitcoinLot
        maybe_create_bitcoin_lot(new_tx, tx_data, db)
    elif new_tx.type in ("Withdrawal", "Sell"):
        # Step 8: If withdrawing or selling BTC, do a FIFO disposal
        maybe_dispose_lots_fifo(new_tx, tx_data, db)
        compute_sell_summary_from_disposals(new_tx, db)
    elif new_tx.type == "Transfer":
        # Step 9: If transferring BTC, move lots and update cost basis
        maybe_transfer_bitcoin_lot(new_tx, tx_data, db)

    # Step 10: For Sell or Withdrawal, compute realized gain summary (post-disposal)
    if new_tx.type in ("Sell", "Withdrawal"):
        compute_sell_summary_from_disposals(new_tx, db)

    db.commit()
    db.refresh(new_tx)
    return new_tx

def update_transaction_record(transaction_id: int, tx_data: dict, db: Session):
    """
    Update an existing Transaction (if not locked).

    Steps:
     - If transaction is locked, return None
     - Re-validate usage & fee rules if relevant fields changed
     - Overwrite header fields on the existing Transaction
     - Rebuild ledger lines from scratch
     - Possibly skip net-zero if cross-currency
     - Re-run lot creation or disposal logic if deposit/buy or withdrawal/sell
     - If it's a disposal (Sell or Withdrawal), recompute realized gains summary
     - Recalculate all subsequent Sell and Withdrawal transactions to ripple updates forward
    """
    tx = get_transaction_by_id(db, transaction_id)  # <--- Fix: pass (db, transaction_id)
    if not tx or tx.is_locked:
        return None

    # Re-validate transaction type & fee if changed
    if any(k in tx_data for k in ("type","from_account_id","to_account_id")):
        _enforce_transaction_type_rules(tx_data, db)
    if any(k in tx_data for k in ("fee_amount","fee_currency","type")):
        _enforce_fee_rules(tx_data, db)

    # Overwrite relevant fields on Transaction
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

    tx.updated_at = datetime.utcnow()

    # Rebuild ledger lines & lot usage from scratch for the current transaction
    remove_ledger_entries_for_tx(tx, db)
    remove_lot_usage_for_tx(tx, db)
    build_ledger_entries_for_transaction(tx, tx_data, db)
    _maybe_verify_balance_for_internal(tx, db)

    # Re-run creation/disposal logic for the current transaction
    if tx.type in ("Deposit", "Buy"):
        maybe_create_bitcoin_lot(tx, tx_data, db)
    if tx.type in ("Withdrawal", "Sell"):
        maybe_dispose_lots_fifo(tx, tx_data, db)

    # If disposal, compute realized gains summary for the current transaction
    if tx.type in ("Sell", "Withdrawal"):
        compute_sell_summary_from_disposals(tx, db)

    # Recalculate all subsequent Sell and Withdrawal transactions
    recalculate_subsequent_transactions(tx, db)

    db.commit()
    db.refresh(tx)
    return tx

def delete_transaction_record(transaction_id: int, db: Session):
    """
    Delete a transaction if not locked. Also removes ledger entries,
    lots, and disposals referencing it.
    """
    tx = get_transaction_by_id(db, transaction_id)  # <--- Fix: pass (db, transaction_id)
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
    If a 'BTC Fees' account doesn't exist, create it. Allows any
    fee ledger line referencing 'BTC Fees' to avoid FK issues.
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
    """Remove all LedgerEntry lines for this transaction."""
    for entry in list(tx.ledger_entries):
        db.delete(entry)
    db.flush()

def remove_lot_usage_for_tx(tx: Transaction, db: Session):
    """Remove any partial-lot disposals or newly created lots for this transaction."""
    for disp in list(tx.lot_disposals):
        db.delete(disp)
    for lot in list(tx.bitcoin_lots_created):
        db.delete(lot)
    db.flush()

def build_ledger_entries_for_transaction(tx: Transaction, tx_data: dict, db: Session):
    """
    Convert single-entry style fields => multi-line ledger. 
    Subtract the fee from proceeds in a Sell, so net is credited to 'to_acct'.
    """
    from_acct_id = tx_data.get("from_account_id")
    to_acct_id   = tx_data.get("to_account_id")
    tx_type      = tx_data.get("type", "")
    amount       = Decimal(tx_data.get("amount", 0))
    fee_amount   = Decimal(tx_data.get("fee_amount", 0))
    fee_currency = (tx_data.get("fee_currency") or "BTC").upper()

    # If user typed gross proceeds, we handle net= (proceeds - fee)
    proceeds_str = tx_data.get("proceeds_usd", "0")
    proceeds_usd = Decimal(proceeds_str) if proceeds_str else Decimal("0")

    from_acct = db.query(Account).filter(Account.id == from_acct_id).first() if from_acct_id else None
    to_acct   = db.query(Account).filter(Account.id == to_acct_id).first()   if to_acct_id else None

    # 1) Transfer with BTC fee
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

    # 2) Sell => from BTC to USD, fees in USD
    if (
        tx_type == "Sell"
        and from_acct and from_acct.currency == "BTC"
        and to_acct and to_acct.currency == "USD"
    ):
        # Subtract 'amount' BTC from the BTC account
        if amount > 0:
            db.add(LedgerEntry(
                transaction_id=tx.id,
                account_id=from_acct.id,
                amount=-amount,
                currency="BTC",
                entry_type="MAIN_OUT"
            ))

        net_usd_in = proceeds_usd  # start with the user's gross proceeds

        # If fee is in USD, reduce net proceeds
        if fee_currency == "USD":
            net_usd_in = proceeds_usd - fee_amount
            if net_usd_in < 0:
                net_usd_in = Decimal("0")

        # **Important**: Update tx_data so disposal sees net proceeds
        tx_data["proceeds_usd"] = str(net_usd_in)

        # Credit the net proceeds to the to_acct
        if net_usd_in > 0:
            db.add(LedgerEntry(
                transaction_id=tx.id,
                account_id=to_acct.id,
                amount=net_usd_in,
                currency="USD",
                entry_type="MAIN_IN"
            ))

        # Fee line to "USD Fees" if >0
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

    # 3) Buy => from USD to BTC, fee in USD
    if (
        tx_type == "Buy"
        and from_acct
        and from_acct.currency == "USD"
        and to_acct
        and to_acct.currency == "BTC"
    ):
        amount_btc      = Decimal(tx_data.get("amount", "0"))
        fee_amount      = Decimal(tx_data.get("fee_amount", "0"))
        cost_basis_usd  = Decimal(tx_data.get("cost_basis_usd", "0"))

        # total_usd_out = user typed cost basis + fee
        total_usd_out = cost_basis_usd + fee_amount

        # Subtract total from the from_acct
        db.add(LedgerEntry(
            transaction_id=tx.id,
            account_id=from_acct.id,
            amount=-total_usd_out,
            currency="USD",
            entry_type="MAIN_OUT"
        ))

        # Credit the purchased BTC
        if amount_btc > 0:
            db.add(LedgerEntry(
                transaction_id=tx.id,
                account_id=to_acct.id,
                amount=amount_btc,
                currency="BTC",
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

    # 4) Fallback for deposits/withdrawals/other
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
        # Decide "BTC Fees" vs. "USD Fees"
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
    If deposit/buy => create a BitcoinLot if to_acct=BTC.
    cost_basis_usd is used to track how many USD were effectively spent.
    NEW: If the user typed a fee in USD for a Buy, we add it to the cost basis
    so the user’s final lot's cost_basis_usd = (typed cost_basis_usd + fee_amount).
    """
    to_acct = db.query(Account).filter(Account.id == tx.to_account_id).first()
    if not to_acct or to_acct.currency != "BTC":
        return

    btc_amount = tx.amount or Decimal("0")
    if btc_amount <= 0:
        return

    # ------------------------------------------------------------
    # If it's a Buy, automatically add the fee (if USD) to cost basis
    # so the user’s final lot basis includes the fee.
    # ------------------------------------------------------------
    cost_basis = Decimal(tx_data.get("cost_basis_usd", "0"))
    fee_cur = (tx_data.get("fee_currency") or "").upper()
    fee_amt = Decimal(tx_data.get("fee_amount", "0"))

    # Only add fee_amt to cost basis if it's a Buy with fee_currency=USD
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
    If withdrawal/sell => do a FIFO partial-lot disposal if from_acct=BTC.

    Pulls 'proceeds_usd' from tx_data. For a Sell, we
    just netted out the fee in build_ledger_entries_for_transaction,
    so partial-lot disposal sees net proceeds -> correct realized gains.
    """
    from_acct = db.query(Account).filter(Account.id == tx.from_account_id).first()
    if not from_acct or from_acct.currency != "BTC":
        return

    btc_outflow = float(tx.amount or 0)
    if btc_outflow <= 0:
        return

    total_proceeds = float(tx_data.get("proceeds_usd", 0))

    # Special case if it's a BTC withdrawal with purpose=Spent & BTC fee
    withdrawal_purpose = (tx.purpose or "").strip()
    if tx.type == "Withdrawal" and withdrawal_purpose == "Spent":
        fee_btc = float(tx.fee_amount or 0)
        fee_cur = (tx.fee_currency or "").upper()
        if fee_btc > 0 and fee_cur == "BTC" and btc_outflow > 0 and total_proceeds > 0:
            # Convert the BTC fee portion to USD, subtract from proceeds
            implied_price = total_proceeds / btc_outflow
            fee_in_usd = fee_btc * implied_price
            net_proceeds = total_proceeds - fee_in_usd
            if net_proceeds < 0:
                net_proceeds = 0.0
            total_proceeds = net_proceeds

    # Retrieve lots FIFO
    lots = db.query(BitcoinLot).filter(BitcoinLot.remaining_btc > 0).order_by(BitcoinLot.acquired_date).all()

    remaining_outflow = btc_outflow
    total_outflow = btc_outflow

    for lot in lots:
        if remaining_outflow <= 0:
            break

        lot_rem = float(lot.remaining_btc)
        if lot_rem <= 0:
            continue

        can_use = min(lot_rem, remaining_outflow)
        lot_fraction = can_use / lot_rem
        disposal_basis = float(lot.cost_basis_usd) * lot_fraction

        partial_proceeds = 0.0
        if total_outflow > 0:
            partial_proceeds = (can_use / total_outflow) * total_proceeds

        disposal_gain = partial_proceeds - disposal_basis

        # Zero gains for Gift/Donation/Lost
        if tx.type == "Withdrawal" and withdrawal_purpose in ("Gift", "Donation", "Lost"):
            disposal_gain = 0.0

        disp = LotDisposal(
            lot_id=lot.id,
            transaction_id=tx.id,
            disposed_btc=Decimal(can_use),
            disposal_basis_usd=Decimal(disposal_basis),
            proceeds_usd_for_that_portion=Decimal(partial_proceeds),
            realized_gain_usd=Decimal(disposal_gain)
        )
        db.add(disp)

        lot.remaining_btc = Decimal(lot_rem - can_use)
        remaining_outflow -= can_use

    db.flush()

def compute_sell_summary_from_disposals(tx: Transaction, db: Session):
    """
    Summarize partial-lot disposals for a Sell/Withdrawal. Overwrite
    tx.cost_basis_usd, tx.proceeds_usd, tx.realized_gain_usd, holding_period.
    """
    disposals = db.query(LotDisposal).filter(LotDisposal.transaction_id == tx.id).all()
    if not disposals:
        return

    total_basis = 0.0
    total_gain = 0.0
    total_proceeds = 0.0
    earliest_date = None

    for disp in disposals:
        total_basis    += float(disp.disposal_basis_usd or 0)
        total_gain     += float(disp.realized_gain_usd or 0)
        total_proceeds += float(disp.proceeds_usd_for_that_portion or 0)

        lot = db.query(BitcoinLot).get(disp.lot_id)
        if lot and (earliest_date is None or lot.acquired_date < earliest_date):
            earliest_date = lot.acquired_date

    tx.cost_basis_usd    = Decimal(total_basis)
    tx.realized_gain_usd = Decimal(total_gain)

    # Overwrite tx.proceeds_usd with sum of partial-lot proceeds
    if total_proceeds:
        tx.proceeds_usd = Decimal(total_proceeds)

    if earliest_date:
        days_held = (tx.timestamp.date() - earliest_date.date()).days
        tx.holding_period = "LONG" if days_held > 365 else "SHORT"
    else:
        tx.holding_period = None

    db.flush()

def maybe_transfer_bitcoin_lot(tx: Transaction, tx_data: dict, db: Session):
    from_acct = db.query(Account).filter(Account.id == tx.from_account_id).first()
    to_acct = db.query(Account).filter(Account.id == tx.to_account_id).first()
    if not from_acct or from_acct.currency != "BTC" or not to_acct or to_acct.currency != "BTC":
        return
    
    btc_outflow = Decimal(tx.amount or 0)
    fee_amount = Decimal(tx.fee_amount or 0) if tx.fee_currency == "BTC" else Decimal(0)
    btc_received = btc_outflow - fee_amount
    if btc_outflow <= 0 or btc_received <= 0:
        return
    
    lots = db.query(BitcoinLot).filter(
        BitcoinLot.remaining_btc > 0,
        BitcoinLot.created_txn_id.in_(
            db.query(Transaction.id).filter(Transaction.to_account_id == tx.from_account_id)
        )
    ).order_by(BitcoinLot.acquired_date).all()
    
    remaining_outflow = btc_outflow
    transferred_cost_basis = Decimal("0")
    
    for lot in lots:
        if remaining_outflow <= 0:
            break
        lot_rem = lot.remaining_btc
        if lot_rem <= 0:
            continue
        
        btc_to_use = min(lot_rem, remaining_outflow)
        fraction = btc_to_use / lot_rem  # Full precision
        cost_basis_portion = lot.cost_basis_usd * fraction
        transferred_cost_basis += cost_basis_portion
        
        lot.remaining_btc -= btc_to_use
        remaining_outflow -= btc_to_use
        db.add(lot)
    
    if remaining_outflow > 0:
        raise HTTPException(status_code=400, detail=f"Not enough BTC to transfer {btc_outflow}")
    
    new_lot_cost_basis = transferred_cost_basis * (btc_received / btc_outflow)  # Full precision
    new_lot = BitcoinLot(
        created_txn_id=tx.id,
        acquired_date=tx.timestamp,
        total_btc=btc_received,
        remaining_btc=btc_received,
        cost_basis_usd=new_lot_cost_basis,  # DB truncates to 2 decimals
    )
    db.add(new_lot)
    
    tx.cost_basis_usd = new_lot_cost_basis  # DB truncates to 2 decimals
    db.add(tx)

# --------------------------------------------------------------------------------
# NEW: Helper Function for Ripple Updates
# --------------------------------------------------------------------------------

def recalculate_subsequent_transactions(updated_tx: Transaction, db: Session):
    """
    Recalculate all Sell and Withdrawal transactions that occur after the updated transaction.
    This ensures that changes to the updated transaction ripple forward, updating cost basis,
    lot disposals, and realized gains for all subsequent transactions.

    Steps:
    1. Query all Sell and Withdrawal transactions with timestamp > updated_tx.timestamp.
    2. For each subsequent transaction:
       a. Remove existing lot disposals.
       b. Re-run FIFO disposal logic.
       c. Recompute realized gains summary.
    """
    # Query all Sell and Withdrawal transactions after the updated transaction's timestamp
    subsequent_txs = db.query(Transaction).filter(
        Transaction.timestamp > updated_tx.timestamp,
        Transaction.type.in_(["Sell", "Withdrawal"])
    ).order_by(Transaction.timestamp).all()

    for sub_tx in subsequent_txs:
        # Remove existing lot disposals for this transaction
        remove_lot_usage_for_tx(sub_tx, db)

        # Re-run FIFO disposal logic for this transaction
        # We need to pass the tx_data for the subsequent transaction
        # Since tx_data isn't stored, we'll use the transaction's attributes
        sub_tx_data = {
            "amount": sub_tx.amount,
            "proceeds_usd": sub_tx.proceeds_usd,
            "fee_amount": sub_tx.fee_amount,
            "fee_currency": sub_tx.fee_currency,
            "purpose": sub_tx.purpose,
            # Add other necessary fields if needed
        }
        maybe_dispose_lots_fifo(sub_tx, sub_tx_data, db)

        # Recompute realized gains summary for this transaction
        compute_sell_summary_from_disposals(sub_tx, db)

# --------------------------------------------------------------------------------
# Double-Entry (with Cross-Currency Skip) & Fee Rules
# --------------------------------------------------------------------------------

def _maybe_verify_balance_for_internal(tx: Transaction, db: Session):
    """
    If type=Buy or Sell => skip net-zero check, cross-currency doesn't net to zero in this approach.
    Otherwise, enforce net=0 for internal (non-99) accounts.
    """
    if tx.type in ("Buy", "Sell"):
        return
    _verify_double_entry_balance_for_internal(tx, db)

def _verify_double_entry_balance_for_internal(tx: Transaction, db: Session):
    """
    Enforces net=0 if from/to are internal. 
    If external=99 => skip. 
    If cross-currency (Buy/Sell) => skip in caller.
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
        db_to   = db.query(Account).get(to_id)
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
