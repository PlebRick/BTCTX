import sys
from pathlib import Path

# --- Ensure imports work even when run directly ---
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]  # e.g. /Users/yourname/BTCTX-org
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --- Correct imports based on your actual project structure ---
from backend.database import SessionLocal
from backend.models.transaction import Transaction, LedgerEntry
from backend.models.account import Account
from backend.models.transaction import BitcoinLot, LotDisposal

# --- Open DB session ---
db = SessionLocal()


# ----------------------------
# Test 1: Ledger Entry Audit
# ----------------------------
def test_ledger_entries_exist():
    """
    Validates expected number of LedgerEntry rows per transaction.
    """
    txs = db.query(Transaction).all()
    actual_count = db.query(LedgerEntry).count()

    def compute_expected_lines(tx: Transaction) -> int:
        fee_amt = float(tx.fee_amount or 0)
        has_fee = fee_amt > 0
        match tx.type:
            case "Buy" | "Sell":
                return 3 if has_fee else 2
            case "Transfer":
                return 3 if has_fee else 2
            case "Deposit" | "Withdrawal":
                return 2 if has_fee else 1
            case _:
                return 1  # Fallback
    total_expected = 0
    mismatches = []

    for tx in txs:
        expected = compute_expected_lines(tx)
        actual = len(tx.ledger_entries)
        total_expected += expected
        if expected != actual:
            mismatches.append((tx.id, tx.type, expected, actual))

    if mismatches:
        print("❌ LedgerEntry mismatches:")
        for tid, ttype, expected, actual in mismatches:
            print(f"  Tx {tid} ({ttype}): expected {expected}, found {actual}")
        raise AssertionError("LedgerEntry mismatch on one or more transactions.")

    if actual_count != total_expected:
        print(f"⚠️ LedgerEntry total mismatch: expected {total_expected}, found {actual_count}")
        raise AssertionError("Mismatch in total ledger entries.")

    print(f"✅ Ledger entries are valid for all {len(txs)} transactions (total = {actual_count}).")


# ----------------------------
# Test 2: BitcoinLot creation
# ----------------------------
def test_bitcoin_lots_created():
    """
    Ensures every Deposit and Buy transaction creates a BitcoinLot.
    """
    txs = db.query(Transaction).all()
    expected_lot_txs = [tx.id for tx in txs if tx.type in ("Deposit", "Buy")]
    lots = db.query(BitcoinLot).all()
    lot_tx_ids = [lot.created_txn_id for lot in lots]
    missing = [txid for txid in expected_lot_txs if txid not in lot_tx_ids]

    if missing:
        print("❌ Missing BitcoinLots for these Deposit/Buy transactions:")
        for txid in missing:
            print(f"  Tx {txid}")
        raise AssertionError("Some Deposit/Buy transactions did not create a BitcoinLot.")

    print(f"✅ BitcoinLots created for all {len(expected_lot_txs)} Deposit/Buy transactions.")


# ----------------------------
# Test 3: LotDisposal creation
# ----------------------------
def test_lot_disposals_exist():
    """
    Ensures LotDisposals are created for:
    - Sell transactions
    - Withdrawals
    - Transfers with BTC fees
    """
    txs = db.query(Transaction).all()
    expected_disposals = []

    for tx in txs:
        if tx.type in ("Sell", "Withdrawal", "Transfer"):
            if tx.type == "Transfer":
                fee_amt = float(tx.fee_amount or 0)
                fee_cur = (tx.fee_currency or "").upper()
                if fee_amt > 0 and fee_cur == "BTC":
                    expected_disposals.append(tx.id)
            else:
                expected_disposals.append(tx.id)

    disposal_tx_ids = [d.transaction_id for d in db.query(LotDisposal).all()]
    missing = [txid for txid in expected_disposals if txid not in disposal_tx_ids]

    if missing:
        print("❌ Missing LotDisposals for expected transactions:")
        for txid in missing:
            print(f"  Tx {txid}")
        raise AssertionError("Some transactions failed to generate LotDisposals.")

    print(f"✅ LotDisposals exist for all expected transactions ({len(expected_disposals)} total).")


# ----------------------------
# Test 4: Account balance integrity
# ----------------------------
def test_account_balances_non_null():
    """
    Ensures that all user-facing accounts have non-zero balances
    after seed data is applied.
    Fee accounts are exempted.
    """
    accounts = db.query(Account).all()
    problems = []

    for acct in accounts:
        if acct.currency in ("BTC", "USD"):
            if acct.name in ("BTC Fees", "USD Fees"):
                continue  # Skip fee accounts
            if abs(acct.balance or 0) == 0:
                problems.append((acct.id, acct.name, acct.currency, acct.balance))

    if problems:
        print("❌ Some main accounts have zero balance after seeding:")
        for aid, name, cur, bal in problems:
            print(f"  Account {aid} ({name}, {cur}) = {bal}")
        raise AssertionError("One or more accounts have zero balance.")

    print(f"✅ All core accounts have non-zero balance (fees excluded).")
