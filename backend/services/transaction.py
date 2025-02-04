from sqlalchemy.orm import Session
from backend.models.transaction import Transaction
from backend.schemas.transaction import TransactionCreate, TransactionUpdate

def get_all_transactions(db: Session):
    """
    Fetch all transactions from the database.
    """
    return db.query(Transaction).all()

def get_transaction_by_id(transaction_id: int, db: Session):
    """
    Fetch a single transaction by its ID.
    """
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()

def create_transaction(transaction: TransactionCreate, db: Session):
    """
    Create a new transaction.
    """
    new_transaction = Transaction(
        account_id=transaction.account_id,
        type=transaction.type,
        amount_usd=transaction.amount_usd,
        amount_btc=transaction.amount_btc,
        purpose=transaction.purpose,
        source=transaction.source,
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction

def update_transaction(transaction_id: int, transaction: TransactionUpdate, db: Session):
    """
    Update an existing transaction.
    """
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not db_transaction:
        return None

    # Update the fields
    db_transaction.type = transaction.type
    db_transaction.amount_usd = transaction.amount_usd
    db_transaction.amount_btc = transaction.amount_btc
    db_transaction.purpose = transaction.purpose
    db_transaction.source = transaction.source

    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def delete_transaction(transaction_id: int, db: Session):
    """
    Delete a transaction by its ID.
    """
    db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if db_transaction:
        db.delete(db_transaction)
        db.commit()
        return True
    return False