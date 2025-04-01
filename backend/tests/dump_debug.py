import sys
from pathlib import Path
from collections import defaultdict
from decimal import Decimal

# Fix import path
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import SessionLocal
from backend.models.transaction import Transaction, LedgerEntry, BitcoinLot, LotDisposal
from backend.models.account import Account

db = SessionLocal()

def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"🧾 {title}")
    print("=" * 60)

def dump_bitcoin_lots():
    lots = db.query(BitcoinLot).all()
    print_header("BitcoinLots")
    for lot in lots:
        print(f"Lot ID={lot.id} | TX ID={lot.created_txn_id} | "
              f"Total={lot.total_btc} | Remaining={lot.remaining_btc} | "
              f"Basis=${lot.cost_basis_usd} | Date={lot.acquired_date.date()}")

def dump_lot_disposals():
    disposals = db.query(LotDisposal).all()
    tx_map = defaultdict(list)
    for d in disposals:
        tx_map[d.transaction_id].append(d)

    print_header("LotDisposals by Transaction")
    for tx_id, records in tx_map.items():
        print(f"TX ID {tx_id} → {len(records)} disposal(s):")
        for d in records:
            print(f"  Lot {d.lot_id} | -{d.disposed_btc} BTC | "
                  f"Basis ${d.disposal_basis_usd} → Proceeds ${d.proceeds_usd_for_that_portion} | "
                  f"Gain ${d.realized_gain_usd}")

def dump_account_balances():
    ledger_entries = db.query(LedgerEntry).all()
    accounts = db.query(Account).all()
    balances = defaultdict(Decimal)

    for e in ledger_entries:
        balances[e.account_id] += Decimal(e.amount)

    print_header("Account Balances (from Ledger)")
    for acct in accounts:
        bal = balances[acct.id]
        print(f"Account ID={acct.id} | {acct.name} ({acct.currency}) = {bal}")

def dump_disposal_mismatch_check():
    transactions = db.query(Transaction).all()
    disposals = db.query(LotDisposal).all()
    tx_disposals = defaultdict(list)
    for d in disposals:
        tx_disposals[d.transaction_id].append(d)

    print_header("Disposal Mismatch Check")
    for tx in transactions:
        if tx.type not in ("Sell", "Withdrawal", "Transfer"):
            continue
        expected = float(tx.amount)
        if tx.fee_currency == "BTC":
            expected += float(tx.fee_amount or 0)
        actual = sum(float(d.disposed_btc) for d in tx_disposals[tx.id])
        status = "✅" if round(expected, 8) == round(actual, 8) else "❌"
        print(f"{status} Tx ID={tx.id} ({tx.type}) → Expected {expected} BTC, Disposed {actual} BTC")

if __name__ == "__main__":
    dump_bitcoin_lots()
    dump_lot_disposals()
    dump_account_balances()
    dump_disposal_mismatch_check()
