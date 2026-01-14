import sys
from pathlib import Path
from decimal import Decimal
from collections import defaultdict
from sqlalchemy import func

# Add project root for absolute imports
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import SessionLocal
from backend.models.transaction import Transaction, LedgerEntry, BitcoinLot, LotDisposal
from backend.models.account import Account

db = SessionLocal()

# ----------------------------
# Test 1: Core Account IDs
# ----------------------------
def test_accounts_exist():
    ids = [acct.id for acct in db.query(Account).all()]
    for expected_id in [1, 2, 3, 4, 5, 6]:
        assert expected_id in ids, f"Missing Account ID={expected_id}"

# ----------------------------
# Test 2: Transaction Count
# ----------------------------
def test_transaction_count():
    txs = db.query(Transaction).all()
    assert len(txs) == 15, f"Expected 15 transactions, found {len(txs)}"

# ----------------------------
# Test 3: BitcoinLots for BTC-acquiring Deposits/Buys
# ----------------------------
def test_bitcoin_lots_created():
    txs = db.query(Transaction).all()
    btc_deposits_or_buys = []
    for tx in txs:
        if tx.type in ("Deposit", "Buy"):
            to_acct = db.get(Account, tx.to_account_id)
            if to_acct and to_acct.currency == "BTC":
                btc_deposits_or_buys.append(tx.id)

    lots = db.query(BitcoinLot).all()
    lot_tx_ids = [lot.created_txn_id for lot in lots]
    missing = [txid for txid in btc_deposits_or_buys if txid not in lot_tx_ids]
    assert not missing, f"Missing BitcoinLots for Deposit/Buy BTC transactions: {missing}"

# ----------------------------
# Test 4: FIFO Lots and Disposals Exist
# ----------------------------
def test_fifo_lot_tracking():
    lots = db.query(BitcoinLot).all()
    disposals = db.query(LotDisposal).all()
    assert lots, "Expected at least one BitcoinLot"
    assert disposals, "Expected at least one LotDisposal"

# ----------------------------
# Test 5: FMV Rules on Non-Sale Withdrawals
# ----------------------------
def test_fmv_logic_present_for_non_sale_withdrawals():
    withdrawals = db.query(Transaction).filter(Transaction.type == "Withdrawal").all()
    for tx in withdrawals:
        if tx.purpose in ("Gift", "Donation", "Lost"):
            assert tx.proceeds_usd == Decimal("0.00"), f"Expected 0 proceeds on ID {tx.id}"
            assert tx.fmv_usd and tx.fmv_usd > 0, f"Missing FMV on {tx.purpose} withdrawal ID {tx.id}"

# ----------------------------
# Test 6: No Negative Lot Balances
# ----------------------------
def test_no_negative_lot_balances():
    broken = db.query(BitcoinLot).filter(BitcoinLot.remaining_btc < 0).all()
    assert not broken, "One or more lots have negative remaining_btc!"

# ----------------------------
# Test 7: Ledger Entry Count and Per-Tx Match
# ----------------------------
def test_ledger_entries_exist():
    txs = db.query(Transaction).all()
    total_ledger = db.query(LedgerEntry).count()

    def expected_entries(tx):
        fee = float(tx.fee_amount or 0)
        if tx.type in ("Buy", "Sell"):
            return 3 if fee > 0 else 2
        elif tx.type == "Transfer":
            return 3 if fee > 0 else 2
        elif tx.type in ("Deposit", "Withdrawal"):
            return 2 if fee > 0 else 1
        return 1

    expected_total = 0
    mismatches = []
    for tx in txs:
        exp = expected_entries(tx)
        actual = len(tx.ledger_entries)
        expected_total += exp
        if actual != exp:
            mismatches.append((tx.id, tx.type, exp, actual))

    assert not mismatches, f"LedgerEntry mismatches: {mismatches}"
    assert total_ledger == expected_total, f"Total LedgerEntry mismatch: expected {expected_total}, got {total_ledger}"

# ----------------------------
# Test 8: Account Ledger Balances
# ----------------------------
def test_account_balances_non_null():
    accounts = db.query(Account).all()
    ledger_entries = db.query(LedgerEntry).all()
    balances = defaultdict(float)

    for entry in ledger_entries:
        balances[entry.account_id] += float(entry.amount)

    problems = []
    for acct in accounts:
        if acct.name in ("BTC Fees", "USD Fees"):
            continue
        if abs(balances[acct.id]) == 0:
            problems.append((acct.id, acct.name, acct.currency))

    assert not problems, f"Zero balances detected: {problems}"

# ----------------------------
# Test 9: No Locked Transactions
# ----------------------------
def test_locked_flag_respected():
    locked = db.query(Transaction).filter_by(is_locked=True).count()
    assert locked == 0, f"{locked} transactions are unexpectedly locked."

# ----------------------------
# Test 10: LotDisposal vs BTC Amount Consistency
# ----------------------------
def test_disposal_amount_matches_transaction():
    txs = db.query(Transaction).all()
    all_disposals = db.query(LotDisposal).all()
    tx_disposals = defaultdict(list)

    for disp in all_disposals:
        tx_disposals[disp.transaction_id].append(disp)

    problems = []

    for tx in txs:
        if tx.type not in ("Sell", "Withdrawal", "Transfer"):
            continue

        if tx.id not in tx_disposals:
            problems.append((tx.id, "Missing LotDisposals"))
            continue

        total_disposed = sum(float(d.disposed_btc) for d in tx_disposals[tx.id])
        fee_btc = float(tx.fee_amount or 0) if (tx.fee_currency or "").upper() == "BTC" else 0.0

        # Compute expected disposal amount
        if tx.type in ("Sell", "Withdrawal"):
            expected_disposal = float(tx.amount or 0) + fee_btc
        elif tx.type == "Transfer":
            expected_disposal = fee_btc  # Transfer only disposes fee, not the transferred amount

        if round(total_disposed, 8) != round(expected_disposal, 8):
            problems.append((tx.id, f"Disposed {total_disposed}, expected {expected_disposal}"))

    assert not problems, f"LotDisposal mismatch: {problems}"

# ----------------------------
# Final Teardown
# ----------------------------
def teardown_module(module):
    db.close()
