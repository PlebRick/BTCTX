"""
services/transaction.py

Business logic for creating, retrieving, updating, and deleting transactions.
Now includes:
 - No more fee_currency.
 - cost_basis_usd integrated.
 - Simple placeholders for recalculation & locking logic.
 - A stub function to determine short/long-term gains for future expansions.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from backend.models.transaction import Transaction, TransactionType
from backend.schemas.transaction import TransactionCreate, TransactionUpdate


def get_all_transactions(db: Session):
    """
    Fetch all transactions in the database.
    """
    return db.query(Transaction).all()

def get_transaction_by_id(transaction_id: int, db: Session):
    """
    Fetch a single transaction by its ID.
    """
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()

def create_transaction_record(transaction_data: TransactionCreate, db: Session):
    """
    Create a new transaction based on incoming TransactionCreate schema.
    This includes cost_basis_usd if provided, 
    and a single fee in USD.

    We'll add placeholders for locked or recalculation later.
    """
    # Potential check: if transaction_data.is_locked is True, we might ignore or reset it, since new tx typically start unlocked.
    new_transaction = Transaction(
        account_id=transaction_data.account_id,
        type=transaction_data.type,
        amount_usd=transaction_data.amount_usd,
        amount_btc=transaction_data.amount_btc,
        timestamp=transaction_data.timestamp,
        source=transaction_data.source,
        purpose=transaction_data.purpose,
        fee=transaction_data.fee,
        cost_basis_usd=transaction_data.cost_basis_usd,
        is_locked=transaction_data.is_locked
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    # Placeholder: call a recalc function for cost basis if needed
    return new_transaction

def update_transaction_record(transaction_id: int, transaction_data: TransactionUpdate, db: Session):
    """
    Update an existing transaction with partial fields from TransactionUpdate.
    If the transaction is locked, we skip or raise an error (placeholder).
    """
    db_transaction = get_transaction_by_id(transaction_id, db)
    if not db_transaction:
        return None

    # If is_locked is True, you might skip or raise an error:
    if db_transaction.is_locked:
        # future logic: raise an exception or return None
        return None

    # Apply partial updates only to provided fields
    if transaction_data.type is not None:
        db_transaction.type = transaction_data.type
    if transaction_data.amount_usd is not None:
        db_transaction.amount_usd = transaction_data.amount_usd
    if transaction_data.amount_btc is not None:
        db_transaction.amount_btc = transaction_data.amount_btc
    if transaction_data.timestamp is not None:
        db_transaction.timestamp = transaction_data.timestamp
    if transaction_data.source is not None:
        db_transaction.source = transaction_data.source
    if transaction_data.purpose is not None:
        db_transaction.purpose = transaction_data.purpose
    if transaction_data.fee is not None:
        db_transaction.fee = transaction_data.fee
    if transaction_data.cost_basis_usd is not None:
        db_transaction.cost_basis_usd = transaction_data.cost_basis_usd
    if transaction_data.is_locked is not None:
        db_transaction.is_locked = transaction_data.is_locked

    db.commit()
    db.refresh(db_transaction)
    # Placeholder: re-run cost basis recalc from earliest unlocked transaction date if needed
    return db_transaction

def delete_transaction_record(transaction_id: int, db: Session):
    """
    Delete a transaction by its ID.
    Placeholder: check if locked before deleting.
    """
    db_transaction = get_transaction_by_id(transaction_id, db)
    if not db_transaction:
        return False

    if db_transaction.is_locked:
        # If locked, do not delete (future logic).
        return False

    db.delete(db_transaction)
    db.commit()
    return True


# --- Recalculation & Short/Long-Term Gains Stubs ---

def recalc_cost_basis_after_edit(db: Session):
    """
    Placeholder for cost basis recalculation logic.
    This might:
      1. Find earliest unlocked transaction date
      2. Re-run FIFO logic for each subsequent deposit/withdrawal
      3. Update cost basis or gain/loss fields accordingly
    """
    pass

def determine_short_or_long_term(acquired_date: datetime, disposed_date: datetime) -> str:
    """
    Simple function to determine if the holding is short-term or long-term.
    If the difference is > 365 days, we consider it long-term; otherwise short-term.
    This is a placeholder for a future advanced approach, including leap years, etc.
    """
    holding_period = disposed_date - acquired_date
    if holding_period > timedelta(days=365):
        return "long-term"
    else:
        return "short-term"
