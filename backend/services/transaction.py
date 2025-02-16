"""
services/transaction.py

Refactored for Double-Entry (Plan B):
  - Replaces the single 'account_id' field with 'from_account_id' and 'to_account_id'.
  - Minimally updates balances in the from/to accounts (if desired).
  - Preserves fee, cost_basis_usd, and locking placeholders.
  - Future expansions can handle detailed cost basis recalculations, short/long-term gains, etc.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
# Import the updated Transaction model with from_account_id/to_account_id
from backend.models.transaction import Transaction, TransactionType
# Import updated schemas that have from_account_id/to_account_id
from backend.schemas.transaction import TransactionCreate, TransactionUpdate
# If we plan to adjust balances, we need the Account model
from backend.models.account import AccountType, Account

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
    Create a new transaction based on TransactionCreate schema.
    Key Differences in Double-Entry:
      - We no longer have 'account_id'; we have 'from_account_id' and 'to_account_id'.
      - If you want, we can update the from_account's balance (subtract) and the to_account's balance (add).
      - cost_basis_usd remains relevant for external BTC deposits or trades.
      - fee is always in USD, so we adjust the from_account's USD if needed.

    Steps:
      1. Create the Transaction object (with from_account_id and to_account_id).
      2. Optionally update each account's balance (if from/to are not external placeholders).
      3. Commit and return the new transaction.
    """

    # 1. Instantiate a new Transaction (the main difference is using from/to accounts)
    new_transaction = Transaction(
        from_account_id=transaction_data.from_account_id,
        to_account_id=transaction_data.to_account_id,
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

    # 2. (Optional) Update balances on from/to accounts
    #    If from_account or to_account is 'External', you might skip. That logic is up to you.

    from_acct = db.query(Account).get(transaction_data.from_account_id)
    to_acct   = db.query(Account).get(transaction_data.to_account_id)

    if from_acct:
        # Subtract amounts from the from_acct balance
        # e.g., if this is a deposit of BTC from an external source, from_acct might be 'External' (skip).
        # For normal user accounts, we do:
        usd_out = transaction_data.amount_usd
        btc_out = transaction_data.amount_btc

        # Also consider the fee if it directly reduces from_acct in USD:
        if transaction_data.fee and transaction_data.fee > 0:
            usd_out += transaction_data.fee

        # We pass negative amounts to update_balance if we want to reduce from_acct
        from_acct.update_balance(amount_usd=-usd_out, amount_btc=-btc_out)

    if to_acct:
        # Add amounts to the to_acct balance
        usd_in = transaction_data.amount_usd
        btc_in = transaction_data.amount_btc
        # Typically, fee doesn't get added to the to_acct, but if you handle fees differently, adjust logic
        to_acct.update_balance(amount_usd=usd_in, amount_btc=btc_in)

    db.commit()
    db.refresh(new_transaction)
    # Placeholder: call a recalc function for cost basis if needed
    return new_transaction

def update_transaction_record(transaction_id: int, transaction_data: TransactionUpdate, db: Session):
    """
    Update an existing transaction with partial fields from TransactionUpdate.
    If the transaction is locked, skip or return None.

    With double-entry:
      - Potentially allow changing from_account_id and to_account_id
        (though real systems rarely let you do that post-creation).
      - If from/to accounts/amounts change, we might need to
        revert the old balances and apply the new balances.
        For simplicity, we won't do that here — we can just show how
        you might handle it if needed.
    """
    db_transaction = get_transaction_by_id(transaction_id, db)
    if not db_transaction:
        return None

    # If is_locked is True, skip or raise error
    if db_transaction.is_locked:
        return None

    # Reverting old amounts from the old from/to accounts is complicated
    # We'll do a minimal approach: we only adjust balances if from/to or amounts changed,
    # ignoring complexities. For a robust approach, you'd do the following steps:
    #   1. Subtract the old amounts from old accounts
    #   2. Add the new amounts to the new accounts
    # For now, let's skip that unless you specifically want it.

    old_from_id = db_transaction.from_account_id
    old_to_id   = db_transaction.to_account_id
    old_usd     = float(db_transaction.amount_usd or 0.0)
    old_btc     = float(db_transaction.amount_btc or 0.0)
    old_fee     = float(db_transaction.fee or 0.0)

    # 1. Apply partial updates
    if transaction_data.from_account_id is not None:
        db_transaction.from_account_id = transaction_data.from_account_id
    if transaction_data.to_account_id is not None:
        db_transaction.to_account_id = transaction_data.to_account_id
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

    # 2. Minimal approach to re-balancing (this is optional and simplistic):
    #    If from_account_id / to_account_id or amounts changed, we can attempt to correct balances.
    #    For a thorough approach, you'd do:
    #       - Revert old_from_acct/update_balance(+old amounts)
    #       - Revert old_to_acct/update_balance(-old amounts)
    #       - Apply new_from_acct/update_balance(-new amounts)
    #       - Apply new_to_acct/update_balance(+new amounts)
    #    Here, we won't do it all unless you want it. We'll just do a placeholder.

    db.commit()
    db.refresh(db_transaction)
    # Placeholder: re-run cost basis recalc if needed
    return db_transaction

def delete_transaction_record(transaction_id: int, db: Session):
    """
    Delete a transaction by its ID.
    If locked, skip deletion.

    For double-entry, you'd also want to revert the old from/to balances
    if you allow transaction deletion. For now, we skip that step
    (or assume you rarely delete real transactions).
    """
    db_transaction = get_transaction_by_id(transaction_id, db)
    if not db_transaction:
        return False

    if db_transaction.is_locked:
        return False

    db.delete(db_transaction)
    db.commit()
    return True

# --- Recalculation & Short/Long-Term Gains Stubs ---

def recalc_cost_basis_after_edit(db: Session):
    """
    Placeholder for cost basis recalculation logic.
    You might:
      1. Find earliest unlocked transaction date
      2. Re-run FIFO logic for each subsequent deposit/withdrawal
      3. Update cost basis or gain/loss fields.
    """
    pass

def determine_short_or_long_term(acquired_date: datetime, disposed_date: datetime) -> str:
    """
    Simple function to determine if the holding is short-term or long-term.
    If the difference is > 365 days, we consider it long-term; otherwise short-term.
    """
    holding_period = disposed_date - acquired_date
    if holding_period > timedelta(days=365):
        return "long-term"
    else:
        return "short-term"
