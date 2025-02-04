from sqlalchemy.orm import Session
from backend.models.account import Account
from backend.schemas.account import AccountCreate, AccountUpdate

def get_all_accounts(db: Session):
    return db.query(Account).all()

def get_account_by_id(account_id: int, db: Session):
    return db.query(Account).filter(Account.id == account_id).first()

def create_account(account: AccountCreate, db: Session):
    new_account = Account(
        user_id=account.user_id,
        type=account.type,
        balance_usd=account.balance_usd,
        balance_btc=account.balance_btc,
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account

def update_account(account_id: int, account: AccountUpdate, db: Session):
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if not db_account:
        return None
    db_account.type = account.type
    db_account.balance_usd = account.balance_usd
    db_account.balance_btc = account.balance_btc
    db.commit()
    db.refresh(db_account)
    return db_account

def delete_account(account_id: int, db: Session):
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if db_account:
        db.delete(db_account)
        db.commit()
        return True
    return False