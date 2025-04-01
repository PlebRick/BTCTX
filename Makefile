# -----------------------------------------------------------------------------
# 💡 BitcoinTX Makefile Commands (Cheat Sheet)
# -----------------------------------------------------------------------------
# make audit         → Full audit loop: wipe DB, create default user + accounts, seed, run tests
# make reset-dev     → Fast rebuild: recreate DB → seed → test
# make reset-tx      → Re-run transactions + tests (no DB wipe or user reinit needed)
# make clean-db      → Delete SQLite database
# make create-db     → Run create_tables() (inserts default user + accounts)
# make seed-tx       → Load seed_transactions.json into DB
# make seed          → Shorthand for create-db → seed-tx
# make test          → Run all audit tests (ledger, lots, disposals, balances)
# make audit-fast    → Run tests but stop on first failure (quicker feedback)
# make debug         → Dump debug view: lots, balances, disposal mismatches
# make export        → Save audit output as JSON/CSV (if export script is enabled)
# make check-locks   → Print number of locked transactions in the database
# -----------------------------------------------------------------------------

.PHONY: audit clean-db seed test export debug create-db seed-tx reset-dev reset-tx audit-fast check-locks

# 💥 Full audit pipeline
audit: clean-db seed test

# 🧼 Delete the SQLite database
clean-db:
	rm -f backend/bitcoin_tracker.db

# 🧪 Recreate DB schema + default user + accounts, then seed TXs
seed: create-db seed-tx

# 🛠️ Run create_tables() (tables, admin user, accounts)
create-db:
	python backend/create_db.py

# 📥 Load predefined test transactions
seed-tx:
	python backend/tests/seed_transactions.py

# ✅ Run audit test suite
test:
	pytest backend/tests/test_seed_data_integrity.py

# 🔄 Rebuild DB, seed, test (fast dev reset)
reset-dev: clean-db seed test

# 🔁 Only reseed + test (no DB wipe)
reset-tx: seed-tx test

# ⚡ Run test suite but stop on first failure
audit-fast:
	pytest backend/tests/test_seed_data_integrity.py --maxfail=1 -q

# 🪵 Dump balances, BTC lots, FIFO disposals
debug:
	python backend/tests/dump_debug.py

# 📤 Export report files (CSV, JSON, etc.)
export:
	python backend/tests/export_results.py

# 🔒 Count locked transactions
check-locks:
	python -c "from backend.database import SessionLocal; from backend.models.transaction import Transaction; db = SessionLocal(); locked = db.query(Transaction).filter_by(is_locked=True).all(); print(f'{len(locked)} locked transaction(s)'); db.close()"
