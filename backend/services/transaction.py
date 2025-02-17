"""
backend/services/transaction.py

Service functions to handle Transaction operations.
This includes creating transactions with dual entries, updating account balances,
and performing FIFO cost basis calculations for BTC sales.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from backend.models.transaction import Transaction
from backend.models.account import Account

def get_all_transactions(db: Session):
    """Retrieve all transactions ordered by timestamp descending."""
    return db.query(Transaction).order_by(Transaction.timestamp.desc()).all()

def get_transaction_by_id(transaction_id: int, db: Session):
    """Retrieve a single transaction by its ID."""
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()

def create_transaction_record(tx_data, db: Session):
    """
    Create a new transaction record.
    
    tx_data is assumed to be a dict or an object (e.g., Pydantic model) with fields:
      - from_account_id
      - to_account_id
      - type (e.g., "BUY", "SELL", "DEPOSIT", "WITHDRAWAL", "TRANSFER")
      - amount
      - fee_amount, fee_currency, external_ref, etc.
      - proceeds_usd (for SELL/BUY)
      - cost_basis_usd (for BUY/DEPOSIT)
    
    For trade types (BUY/SELL) or transfers, this function may create two related entries,
    linking them via group_id.
    """
    # Create a new Transaction object from the provided data.
    new_tx = Transaction(
        from_account_id = tx_data.get("from_account_id"),
        to_account_id = tx_data.get("to_account_id"),
        type = tx_data.get("type"),
        amount = tx_data.get("amount"),
        timestamp = tx_data.get("timestamp", datetime.utcnow()),
        fee_amount = tx_data.get("fee_amount"),
        fee_currency = tx_data.get("fee_currency"),
        external_ref = tx_data.get("external_ref"),
        cost_basis_usd = tx_data.get("cost_basis_usd"),
        proceeds_usd = tx_data.get("proceeds_usd")
    )
    
    # Add the new transaction
    db.add(new_tx)
    db.flush()  # Get an ID assigned
    
    # For dual-entry transactions (like BUY, SELL, TRANSFER), you might create a paired entry.
    # For simplicity, if tx_data includes both from_account_id and to_account_id, we treat this single record as the full entry.
    # (Alternatively, you could create a matching record with swapped account IDs.)
    
    # Here we set group_id to the transaction's own ID for grouping.
    new_tx.group_id = new_tx.id
    
    # For SELL transactions, calculate realized gain via FIFO if applicable.
    if new_tx.type.upper() in ("SELL",):
        calculate_cost_basis_and_gain(db, new_tx)
    
    db.commit()
    db.refresh(new_tx)
    return new_tx

def calculate_cost_basis_and_gain(db: Session, tx: Transaction):
    """
    For a SELL transaction, allocate sold BTC from prior BUY/DEPOSIT lots (FIFO)
    and compute the cost basis, proceeds, realized gain, and holding period.
    
    This function queries prior BTC inflow transactions (of type BUY or DEPOSIT)
    for the same account (assumed to be the BTC account from which the sale occurs),
    then allocates the sold amount from the oldest available lots.
    
    For simplicity, this example assumes that each inflow transaction is fully available
    until a sale uses it, and that a sale may consume one or more lots.
    
    Note: In production, you might store a remaining amount on each lot or split the sale into multiple records.
    """
    # Ensure this is a SELL transaction.
    if tx.type.upper() != "SELL":
        return

    btc_to_sell = float(tx.amount)
    cost_basis_total = 0.0
    lots_consumed = []  # To record details for audit

    # Query for previous BTC inflow transactions (BUY or DEPOSIT) for the same BTC account.
    # We assume the BTC account is the one from which funds are sold (from_account_id).
    lots = db.query(Transaction).filter(
        Transaction.to_account_id == tx.from_account_id,
        Transaction.type.in_(["BUY", "DEPOSIT"]),
        Transaction.cost_basis_usd != None
    ).order_by(Transaction.timestamp).all()

    for lot in lots:
        # For this example, assume the full lot amount is available (i.e. no partial consumption is tracked).
        available = float(lot.amount)
        if btc_to_sell <= 0:
            break
        use_amount = min(available, btc_to_sell)
        lot_fraction = use_amount / available
        cost_basis_portion = float(lot.cost_basis_usd) * lot_fraction
        cost_basis_total += cost_basis_portion
        lots_consumed.append((lot.id, use_amount, cost_basis_portion))
        btc_to_sell -= use_amount

    # If more BTC is sold than available, raise an error (should be validated beforehand).
    if btc_to_sell > 0:
        raise Exception("Insufficient BTC in lots to cover sale")

    # Set cost_basis and realized gain on the sale transaction.
    tx.cost_basis_usd = round(cost_basis_total, 2)
    proceeds = float(tx.proceeds_usd) if tx.proceeds_usd is not None else 0.0
    tx.realized_gain_usd = round(proceeds - cost_basis_total, 2)

    # Determine holding period based on the oldest lot used.
    if lots_consumed:
        first_lot_id = lots_consumed[0][0]
        first_lot = db.query(Transaction).filter(Transaction.id == first_lot_id).first()
        if first_lot:
            days_held = (tx.timestamp.date() - first_lot.timestamp.date()).days
            tx.holding_period = "LONG" if days_held > 365 else "SHORT"
        else:
            tx.holding_period = None
    else:
        tx.holding_period = None

def update_transaction_record(transaction_id: int, tx_data, db: Session):
    """
    Update an existing transaction.
    For simplicity, this function does not automatically recalculate account balances.
    In a complete system, reversing the original transaction and applying the new one would be required.
    """
    tx = get_transaction_by_id(transaction_id, db)
    if not tx or tx.is_locked:
        return None
    # Update allowed fields.
    if "amount" in tx_data:
        tx.amount = tx_data["amount"]
    if "type" in tx_data:
        tx.type = tx_data["type"]
    if "fee_amount" in tx_data:
        tx.fee_amount = tx_data["fee_amount"]
    if "fee_currency" in tx_data:
        tx.fee_currency = tx_data["fee_currency"]
    if "external_ref" in tx_data:
        tx.external_ref = tx_data["external_ref"]
    # Additional fields can be updated as needed.
    db.commit()
    db.refresh(tx)
    return tx

def delete_transaction_record(transaction_id: int, db: Session):
    """
    Delete a transaction if it is not locked.
    Note: In a proper double-entry system, deletion should reverse account balances or be disallowed.
    """
    tx = get_transaction_by_id(transaction_id, db)
    if not tx or tx.is_locked:
        return False
    db.delete(tx)
    db.commit()
    return True
