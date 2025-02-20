"""
backend/services/transaction.py

Service functions to handle Transaction operations in the new double-entry system.
They create and retrieve Transaction records, handle cost basis for sells,
and update or delete as needed.
"""

from sqlalchemy.orm import Session
from datetime import datetime
from backend.models.transaction import Transaction
from backend.models.account import Account

def get_all_transactions(db: Session):
    """
    Retrieve all transactions, ordered by timestamp descending.
    With the new model, each Transaction has:
      - from_account_id, to_account_id
      - amount (single numeric)
      - fee_amount, fee_currency
      - cost_basis_usd, proceeds_usd
      - source, purpose (for deposits/withdrawals)
      - is_locked, etc.
    """
    return db.query(Transaction).order_by(Transaction.timestamp.desc()).all()

def get_transaction_by_id(transaction_id: int, db: Session):
    """Retrieve a single transaction by its ID."""
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()

def create_transaction_record(tx_data: dict, db: Session) -> Transaction:
    """
    Create a new transaction record in the database.

    The `tx_data` dict is typically derived from the Pydantic schema
    (TransactionCreate). Expected fields include:
      - from_account_id (int)
      - to_account_id (int)
      - type (str) => 'Deposit', 'Withdrawal', 'Transfer', 'Buy', 'Sell'
      - amount (Decimal) => main transaction amount (in 'from' account's currency)
      - timestamp (datetime, optional) => defaults to now if not given
      - fee_amount (Decimal, optional), fee_currency (str, optional)
      - cost_basis_usd (Decimal, optional) => used for BTC inflows or Buy
      - proceeds_usd (Decimal, optional)   => used for BTC outflows or Sell
      - source (str, optional)  => e.g. 'Gift', 'Income' for Deposit
      - purpose (str, optional) => e.g. 'Spent', 'Donation' for Withdrawal
      - external_ref (str, optional)
      - is_locked (bool, optional)

    This function:
      1) Instantiates a Transaction with these fields.
      2) Commits it to the DB, assigns an ID/group_id.
      3) If it's a SELL, we optionally call calculate_cost_basis_and_gain()
         to determine realized gains via FIFO.

    Returns the newly created Transaction object.
    """

    # 1) Create a new Transaction object from the provided data.
    new_tx = Transaction(
        from_account_id = tx_data.get("from_account_id"),
        to_account_id   = tx_data.get("to_account_id"),
        type            = tx_data.get("type"),
        amount          = tx_data.get("amount"),
        timestamp       = tx_data.get("timestamp", datetime.utcnow()),
        fee_amount      = tx_data.get("fee_amount"),
        fee_currency    = tx_data.get("fee_currency"),
        external_ref    = tx_data.get("external_ref"),

        # Reintroduced deposit/withdrawal fields
        source          = tx_data.get("source"),
        purpose         = tx_data.get("purpose"),

        # Tax-related fields
        cost_basis_usd  = tx_data.get("cost_basis_usd"),
        proceeds_usd    = tx_data.get("proceeds_usd"),
        # realized_gain_usd and holding_period are computed later if SELL
        is_locked       = tx_data.get("is_locked", False),
    )

    # 2) Add and flush so we can get an ID
    db.add(new_tx)
    db.flush()  # so new_tx.id is assigned

    # For simplicity, we set group_id = the same as the tx.id,
    # so it's grouped with itself. If you do multi-row transactions
    # for double-entry, you'd use the same group_id for both rows.
    new_tx.group_id = new_tx.id

    # If type is SELL => compute cost basis and gain
    if new_tx.type and new_tx.type.upper() == "SELL":
        calculate_cost_basis_and_gain(db, new_tx)

    # 3) Commit & refresh
    db.commit()
    db.refresh(new_tx)

    return new_tx

def calculate_cost_basis_and_gain(db: Session, tx: Transaction):
    """
    For a SELL transaction, allocate sold BTC from previous BUY/DEPOSIT "lots"
    on a FIFO basis. Then set:
      - tx.cost_basis_usd
      - tx.realized_gain_usd
      - tx.holding_period = 'LONG' or 'SHORT'
    This is a simplified example. A real system would track partial lot usage,
    leftover amounts, etc.
    """
    # 1) Confirm this is a SELL
    if tx.type.upper() != "SELL":
        return

    # 2) The quantity of BTC sold is tx.amount (the 'from' account is BTC).
    btc_to_sell = float(tx.amount)

    # 3) We'll accumulate cost_basis as we consume "lots"
    cost_basis_total = 0.0

    # 4) Query prior BTC inflows: type=BUY or DEPOSIT, same 'to_account_id' as tx.from_account_id
    lots = db.query(Transaction).filter(
        Transaction.to_account_id == tx.from_account_id,
        Transaction.type.in_(["Buy", "Deposit"]),
        Transaction.cost_basis_usd != None  # Only lots that established a cost basis
    ).order_by(Transaction.timestamp).all()

    # 5) We'll fully consume each lot if possible
    for lot in lots:
        if btc_to_sell <= 0:
            break
        available = float(lot.amount)
        if available <= 0:
            continue  # skip if this lot has 0 left (not tracked in this simplistic approach)

        # We'll use either the entire lot or what's left to sell
        use_amount = min(available, btc_to_sell)
        lot_fraction = use_amount / available

        # We assume cost_basis_usd is for the entire 'lot.amount'
        cost_basis_portion = float(lot.cost_basis_usd) * lot_fraction
        cost_basis_total += cost_basis_portion

        btc_to_sell -= use_amount

    # If there's still BTC left to sell, it means we had no enough lots
    if btc_to_sell > 0:
        raise ValueError("Insufficient BTC in deposit/buy lots to cover this SELL transaction")

    # 6) The sale has proceeds_usd (if provided) and now a total cost_basis_usd
    tx.cost_basis_usd = round(cost_basis_total, 2)
    proceeds = float(tx.proceeds_usd) if tx.proceeds_usd else 0.0
    tx.realized_gain_usd = round(proceeds - cost_basis_total, 2)

    # 7) Holding period => based on earliest lot's date
    if lots:
        earliest_lot = lots[0]
        days_held = (tx.timestamp.date() - earliest_lot.timestamp.date()).days
        tx.holding_period = "LONG" if days_held > 365 else "SHORT"
    else:
        tx.holding_period = None

def update_transaction_record(transaction_id: int, tx_data: dict, db: Session):
    """
    Update an existing transaction (partial update).
    - If is_locked is True, we skip.
    - For SELL, we could re-run cost basis if 'amount' or 'proceeds_usd' changed.
      (This example doesn't do it automatically; you might want to handle that.)
    """
    tx = get_transaction_by_id(transaction_id, db)
    if not tx or tx.is_locked:
        return None

    # Update allowed fields
    if "from_account_id" in tx_data:
        tx.from_account_id = tx_data["from_account_id"]
    if "to_account_id" in tx_data:
        tx.to_account_id = tx_data["to_account_id"]
    if "amount" in tx_data:
        tx.amount = tx_data["amount"]
    if "type" in tx_data:
        tx.type = tx_data["type"]
    if "timestamp" in tx_data:
        tx.timestamp = tx_data["timestamp"]
    if "fee_amount" in tx_data:
        tx.fee_amount = tx_data["fee_amount"]
    if "fee_currency" in tx_data:
        tx.fee_currency = tx_data["fee_currency"]
    if "external_ref" in tx_data:
        tx.external_ref = tx_data["external_ref"]
    if "cost_basis_usd" in tx_data:
        tx.cost_basis_usd = tx_data["cost_basis_usd"]
    if "proceeds_usd" in tx_data:
        tx.proceeds_usd = tx_data["proceeds_usd"]

    # Also handle source / purpose if you want them updatable
    if "source" in tx_data:
        tx.source = tx_data["source"]
    if "purpose" in tx_data:
        tx.purpose = tx_data["purpose"]

    # Re-run cost basis for SELL if you want (this example doesn't)
    # if tx.type.upper() == "SELL":
    #    calculate_cost_basis_and_gain(db, tx)

    db.commit()
    db.refresh(tx)
    return tx

def delete_transaction_record(transaction_id: int, db: Session):
    """
    Delete a transaction if it is not locked.
    In a true double-entry system, you generally never "delete" but rather
    create a reversing transaction. For simplicity, we allow deletion here.
    """
    tx = get_transaction_by_id(transaction_id, db)
    if not tx or tx.is_locked:
        return False

    db.delete(tx)
    db.commit()
    return True
