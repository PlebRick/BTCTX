"""
backend/services/account.py

Manages creation, update, deletion, and retrieval of Accounts.
In a double-entry environment, each Account can appear in many LedgerEntry lines
(e.g. for 'MAIN_IN', 'MAIN_OUT', 'FEE'). The user typically calls these endpoints
via account.py router.

Now refactored to:
 - Auto-create four special accounts if missing: 
   ID=1 => Bank (USD)
   ID=2 => Wallet (BTC)
   ID=3 => Exchange USD (USD)
   ID=4 => Exchange BTC (BTC)
 - Disallow name or currency changes for those four special accounts.
 - Provide an option for normal accounts beyond those four.
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.models.account import Account
from backend.schemas.account import AccountCreate, AccountUpdate


# ---------------------------------------------------------------------
#  Predefined special accounts
# ---------------------------------------------------------------------
SPECIAL_ACCOUNTS = {
    1: {"name": "Bank",         "currency": "USD"},
    2: {"name": "Wallet",       "currency": "BTC"},
    3: {"name": "Exchange USD", "currency": "USD"},
    4: {"name": "Exchange BTC", "currency": "BTC"},
}


def get_all_accounts(db: Session):
    """
    Fetch all accounts in the system.
    We might auto-create or fix the special 4 if they're missing or mislabeled.
    """
    ensure_special_accounts_exist(db)
    return db.query(Account).all()


def get_account_by_id(account_id: int, db: Session):
    """
    Return the Account with the specified ID, or None if it doesn't exist.
    """
    return db.query(Account).filter(Account.id == account_id).first()


def create_account(account_data: AccountCreate, db: Session):
    """
    Create a new Account. The user must supply:
      - user_id: an existing User
      - name: e.g. "Something", not one of the 4 locked accounts
      - currency: "USD" or "BTC"

    If the user tries to create one of the four special IDs
    or name="Bank"/"Wallet"/"Exchange USD"/"Exchange BTC",
    we raise an error because those are auto-managed.
    """
    ensure_special_accounts_exist(db)

    # Prevent user from creating an account with a name or ID that conflicts
    # with the four special accounts:
    forbidden_names = {v["name"] for v in SPECIAL_ACCOUNTS.values()}
    if account_data.name in forbidden_names:
        raise HTTPException(
            status_code=400,
            detail="Cannot manually create one of the locked special accounts."
        )

    new_account = Account(
        user_id=account_data.user_id,
        name=account_data.name,
        currency=account_data.currency,
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account


def update_account(account_id: int, account_data: AccountUpdate, db: Session):
    """
    Update an existing account's fields (name/currency).
    If account doesn't exist, return None.

    If the account is one of the four special accounts (ID=1..4),
    we disallow changing name/currency.
    """
    account = get_account_by_id(account_id, db)
    if not account:
        return None

    # If it's a special account (1..4), block changes to name/currency.
    if account_id in SPECIAL_ACCOUNTS:
        # We can allow user to rename "Bank" => "Bank" again, but
        # let's block any attempt to change it from the official name/currency.
        if account_data.name is not None and account_data.name != account.name:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot rename the special account #{account_id} ({account.name})."
            )
        if account_data.currency is not None and account_data.currency != account.currency:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot change currency of special account #{account_id} ({account.name})."
            )

    # For a normal account, or if we haven't tried to change name/currency:
    if account_data.name is not None:
        account.name = account_data.name
    if account_data.currency is not None:
        account.currency = account_data.currency

    db.commit()
    db.refresh(account)
    return account


def delete_account(account_id: int, db: Session):
    """
    Delete the account by ID if it exists.
    If it's one of the 4 special accounts, we block that deletion.
    """
    account = get_account_by_id(account_id, db)
    if not account:
        return False

    if account_id in SPECIAL_ACCOUNTS:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete special account #{account_id} ({account.name})."
        )

    db.delete(account)
    db.commit()
    return True


# ---------------------------------------------------------------------
# Internal helper to ensure the 4 special accounts exist & are correct
# ---------------------------------------------------------------------
def ensure_special_accounts_exist(db: Session):
    """
    For each of the 4 special accounts:
      - If it doesn't exist, create it with the correct name/currency.
      - If it does exist but has a mismatch in name/currency,
        we attempt to fix or raise an error (your choice).
    """
    for acc_id, info in SPECIAL_ACCOUNTS.items():
        special_acc = get_account_by_id(acc_id, db)
        if not special_acc:
            # Create it
            new_acc = Account(
                id=acc_id,   # Force the ID
                user_id=1,   # or whichever system user
                name=info["name"],
                currency=info["currency"],
            )
            db.add(new_acc)
            try:
                db.commit()
                db.refresh(new_acc)
            except:
                db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to create special account ID={acc_id}. Possibly ID in use."
                )
        else:
            # Confirm the name/currency match. If mismatch => fix or raise.
            if special_acc.name != info["name"]:
                # You can fix it or raise an error. We'll fix it automatically.
                special_acc.name = info["name"]
            if special_acc.currency != info["currency"]:
                special_acc.currency = info["currency"]
            db.commit()
            db.refresh(special_acc)