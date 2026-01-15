# Changelog

All notable changes to BitcoinTX are documented in this file.

## [Unreleased]

### Added
- **Frontend Design System Refactor**: Major code quality and architecture improvements
  - Custom hooks: `useAccounts`, `useApiCall`, `useBtcPrice` for reusable logic
  - Toast notification system with `ToastContext` for user feedback
  - Error boundaries (`ErrorBoundary.tsx`) for graceful error handling
  - Centralized theme system (`theme.css`) with CSS variables
  - Barrel exports via `hooks/index.ts`
- **CSV Export**: Export all transactions as a CSV file matching the import template format
  - Creates clean roundtrip: Export → Edit → Re-import
  - File naming: `btctx_transactions_YYYY-MM-DD.csv`
  - New endpoint: `GET /api/backup/csv`
- **CSV Import Instructions PDF**: Downloadable PDF guide for CSV import feature
  - New endpoint: `GET /api/import/instructions`
- **Pre-Commit Test Suite**: 17 tests for catching regressions
  - Run with: `./scripts/pre-commit.sh` or `python backend/tests/pre_commit_tests.py`

### Fixed
- **Form 8949 non-taxable exclusion**: Gift, Donation, and Lost disposals now correctly excluded
- **Proceeds degradation fix**: Fixed bug where `proceeds_usd` could degrade during recalculation
- **FIFO lot disposal now account-specific**: Fixed bug where selling/withdrawing BTC would consume lots from all accounts globally instead of only from the source account. This ensures correct cost basis tracking when BTC is held across multiple accounts.

### Files Added
- `frontend/src/hooks/useAccounts.ts` - Account fetching and caching hook
- `frontend/src/hooks/useApiCall.ts` - Generic API call hook with loading/error states
- `frontend/src/hooks/useBtcPrice.ts` - BTC price fetching hook
- `frontend/src/hooks/index.ts` - Barrel exports for hooks
- `frontend/src/components/ErrorBoundary.tsx` - React error boundary component
- `frontend/src/components/Toast.tsx` - Toast notification component
- `frontend/src/components/ToastContainer.tsx` - Toast container component
- `frontend/src/contexts/ToastContext.tsx` - Toast context provider
- `frontend/src/styles/theme.css` - Centralized CSS variables and theming
- `frontend/src/styles/toast.css` - Toast notification styles
- `frontend/src/styles/errorBoundary.css` - Error boundary styles
- `backend/tests/pre_commit_tests.py` - Pre-commit test suite
- `scripts/pre-commit.sh` - Shell script wrapper for pre-commit tests

---

## [v0.5.0] - 2025-01-14 - Backend Refactoring & Test Suite

### Major Backend Refactoring

#### Code Modernization
- **Removed passlib dependency**: Direct bcrypt usage for password hashing
  - `User.set_password()` and `User.verify_password()` now use bcrypt directly
  - Added 72-byte password limit validation (bcrypt requirement)
  - Eliminates passlib deprecation warnings
- **Replaced deprecated `Query.get()`**: Updated to `Session.get()` pattern
  - 10 occurrences in `transaction.py`
  - 1 occurrence in `debug.py`
  - 1 occurrence in `test_seed_data_integrity.py`
- **Replaced `@app.on_event` deprecation**: Migrated to FastAPI lifespan context manager
- **Removed duplicate import**: Fixed `from_orm` duplicate in `form_8949.py`

#### Performance Improvements
- **Added `joinedload` eager loading**: Optimized `compute_sell_summary_from_disposals()`
  - Prevents N+1 queries when loading `LotDisposal.lot` relationships
- **Added database indexes on foreign keys**:
  - `LedgerEntry.transaction_id`, `LedgerEntry.account_id`
  - `BitcoinLot.created_txn_id`
  - `LotDisposal.lot_id`, `LotDisposal.transaction_id`

#### Code Organization
- **Created `backend/constants.py`**: Centralized account ID constants
  - `ACCOUNT_BANK`, `ACCOUNT_WALLET`, `ACCOUNT_EXCHANGE_USD`, `ACCOUNT_EXCHANGE_BTC`
  - `ACCOUNT_BTC_FEES`, `ACCOUNT_USD_FEES`, `ACCOUNT_EXTERNAL`
  - Replaced magic numbers throughout codebase
- **Deleted dead files**:
  - `backend/create_account_db.py` (unused)
  - `backend/create_db.py` (replaced with inline command)
- **Updated Makefile**: `create-db` target now uses inline Python command

### CSV Import/Export Fixes
- **Fixed CSV export `proceeds_usd`**: Now falls back to `proceeds_usd` when `gross_proceeds_usd` is None
- **Relaxed CSV import validation**: Now matches transaction service rules
  - Deposit: External → any internal account (BTC or USD)
  - Withdrawal: any internal account → External
  - Transfer: between internal accounts of same currency

### Testing

#### Comprehensive Test Suite (`backend/tests/test_everything.py`)
78 automated tests covering:
- Database seeding with 65 test transactions
- All API endpoints (accounts, transactions, calculations, debug)
- All report generation (Complete Tax Report, IRS Forms, Transaction History)
- CSV export/import roundtrip verification
- FIFO integrity (lots, disposals, account balance matching)
- Gains/losses calculations and income tracking
- All transaction types, withdrawal purposes, deposit sources
- Holding period verification (short-term vs long-term)

Run with: `python3 backend/tests/test_everything.py`

#### Authentication Test Suite (`backend/tests/test_password_migration.py`)
Comprehensive auth tests:
- Password hashing and verification
- 72-byte bcrypt limit enforcement
- Unicode and special character passwords
- Login/logout endpoint tests
- Session persistence tests
- Protected endpoint authentication
- Backward compatibility with existing hashes

Run with: `pytest backend/tests/test_password_migration.py -v`

#### Updated Seed Data (`backend/tests/transaction_seed_data.json`)
- 65 transactions across 2023-2025
- All 5 deposit sources: MyBTC, Gift, Income, Interest, Reward
- All 4 withdrawal purposes: Spent, Gift, Donation, Lost
- Short-term and long-term gains coverage
- USD and BTC deposits to various accounts

### Dependency Updates

| Package | Old Version | New Version |
|---------|-------------|-------------|
| pydantic | 2.10.6 | 2.12.5 |
| uvicorn | 0.34.0 | 0.40.0 |
| sqlalchemy | 2.0.37 | 2.0.45 |
| httpx | 0.24.1 | 0.28.1 |
| requests | 2.28.1 | 2.32.0 |
| python-multipart | 0.0.6 | 0.0.20 |
| python-dateutil | 2.8.2 | 2.9.0 |
| itsdangerous | 2.1.2 | 2.2.0 |
| reportlab | 3.6.12 | 4.4.7 |
| pytest | 8.1.1 | 8.3.5 |

### Removed Dependencies
- `passlib` - replaced with direct bcrypt
- `typer` - unused
- `python-jose` - unused
- `pandas` - unused
- `weasyprint` - unused
- `pdfkit` - unused
- `jinja2` - unused (beyond FastAPI's built-in)
- `pycryptodome` - unused

### Files Added
- `backend/constants.py` - Centralized account ID constants
- `backend/tests/test_everything.py` - Comprehensive test suite (78 tests)
- `backend/tests/test_password_migration.py` - Authentication tests

### Files Modified
- `backend/models/user.py` - Direct bcrypt, 72-byte limit
- `backend/models/transaction.py` - FK indexes
- `backend/database.py` - Direct bcrypt for default user
- `backend/main.py` - Lifespan context manager
- `backend/services/transaction.py` - Query.get(), joinedload, constants
- `backend/routers/backup.py` - proceeds_usd fallback, constants
- `backend/routers/debug.py` - Query.get()
- `backend/services/csv_import.py` - Relaxed validation, constants
- `backend/services/reports/form_8949.py` - Removed duplicate import
- `backend/tests/register_default_user.py` - Direct bcrypt
- `backend/requirements.txt` - Updated all versions
- `Makefile` - Updated create-db target

### Files Deleted
- `backend/create_account_db.py`
- `backend/create_db.py`

---

## [v0.4.0] - 2025-01-12

### Added
- **CSV Template Import**: Bulk transaction import from CSV files
  - Download CSV template with exact column structure
  - Preview parsed transactions before importing
  - Full validation with error/warning display
  - Atomic import (all-or-nothing) with rollback on failure
  - Requires empty database (Phase 1 - no merge complexity)

### Endpoints
- `GET /api/import/template` - Download blank CSV template
- `GET /api/import/status` - Check if database is empty
- `POST /api/import/preview` - Parse and preview CSV (no DB writes)
- `POST /api/import/execute` - Execute atomic import

### Files Added
- `backend/schemas/csv_import.py` - Pydantic request/response models
- `backend/services/csv_import.py` - Parsing, validation, and import logic
- `backend/routers/csv_import.py` - API endpoints

### Fixed
- **Atomic imports**: Added `auto_commit` parameter to `create_transaction_record()`
  - Bulk imports now use `auto_commit=False` to defer commit until all succeed
  - Prevents partial imports on validation failures
- **Async event loop conflict**: Fixed `get_btc_price()` during CSV import
  - Used `ThreadPoolExecutor` to run async price fetches in separate threads
  - Fixes "Cannot run the event loop while another loop is running" error

---

## [v0.3.2] - 2025-01-10

### Fixed
- **Backup restore redirect**: Fixed "Not Found" error after successful backup restore
  - After restoring a backup, the session cookie still referenced the old user_id
  - Backend now clears session after restore (`request.session.clear()`)
  - Frontend redirects to `/login` instead of reloading the page
  - Users now see success message and are redirected to login properly

---

## [v0.3.1] - 2025-01-10

### Fixed
- **Backup/restore in Docker/StartOS**: Fixed `backup.py` to use `DATABASE_FILE` environment variable
  - Previously used hardcoded path `backend/bitcoin_tracker.db` which didn't match Docker's `/data/btctx.db`
  - Backup and restore now work correctly in containerized environments
- **Backup file cleanup race condition**: Fixed temp file deletion before streaming complete
  - Now uses FastAPI `BackgroundTasks` to delete temp file after response completes

### Documentation
- **StartOS container architecture**: Comprehensive documentation in `docs/STARTOS_COMPATIBILITY.md`
  - Two-repository architecture explanation
  - Volume mounts and data persistence
  - DATABASE_FILE environment variable
  - Common mistakes to avoid

---

## [v0.3.0] - 2025 IRS Form Support

### Added
- **Multi-year IRS form support**: Users can now generate IRS reports for both 2024 and 2025 tax years
- Year-based template folder structure (`backend/assets/irs_templates/2024/`, `2025/`)
- `get_template_path(year, form_name)` - Dynamic template path selection
- `get_supported_years()` - Returns list of available tax years
- `get_8949_field_config(year)` - Year-specific Form 8949 field naming
- `get_schedule_d_field_config(year)` - Year-specific Schedule D field naming
- 2025 IRS Form 8949 and Schedule D templates
- Comprehensive test dataset (40 transactions spanning 2023-2025)

### Fixed
- **Schedule D field mapping**: Changed from Line 1b/8b to Line 3/10 for self-tracked crypto
  - Self-custody Bitcoin uses Box C (short-term) and Box F (long-term) - not reported on 1099
  - Line 3 for short-term totals from Box C, Line 10 for long-term totals from Box F
- **Complete Tax Report generation**: Fixed Transfer lot restoration in `_partial_relot_strictly_after()`
  - Transfer transactions now properly restore source lot balances during year-boundary recalculations
  - Uses LIFO to reverse FIFO consumption when rebuilding transactions

### Changed
- `map_8949_rows_to_field_data()` now accepts `year` parameter for correct field naming
- `map_schedule_d_fields()` now accepts `year` parameter
- `fill_8949_multi_page()` now accepts `year` parameter
- `_verify_templates_exist()` now validates year-specific template availability
- IRS reports endpoint returns helpful error for unsupported years

### Technical Details
- 2024 Form 8949: `Table_Line1`, fields `f1_3` (not zero-padded)
- 2025 Form 8949: `Table_Line1_Part1`/`Part2`, fields `f1_03` (zero-padded for row 1)
- Schedule D Line 3 (Row3): Short-term from Box C/I (self-tracked, no 1099)
- Schedule D Line 10 (Row10): Long-term from Box F/L (self-tracked, no 1099)

---

## [v0.2.0-beta] - StartOS Packaging Complete

### Added
- `docs/` directory for project documentation
- `CLAUDE.md` - AI assistant context file (root directory for auto-detection)
- `docs/CHANGELOG.md` - This file
- `docs/ROADMAP.md` - Future goals and planned features
- `docs/STARTOS_COMPATIBILITY.md` - Docker requirements for StartOS packaging

### Changed
- Updated `README.md` with current Docker instructions and accurate tech stack

---

## [2025-01-10] - Docker Compatibility & Cleanup

### Fixed
- **PDF generation paths**: Changed relative paths to absolute paths in `backend/routers/reports.py`
  - IRS Form 8949 and Schedule D templates now load correctly regardless of working directory
  - Added `_verify_pdftk_installed()` and `_verify_templates_exist()` pre-flight checks

- **BTC price fetching in Docker**: Fixed `get_btc_price()` in `backend/services/transaction.py`
  - Previously made HTTP calls to `localhost:8000` which failed in Docker (port 80)
  - Now calls bitcoin service functions directly via import

- **Python 3.9 compatibility**: Added `from __future__ import annotations` to:
  - `backend/schemas/transaction.py`
  - `backend/services/user.py`
  - Fixes `TypeError: unsupported operand type(s) for |` for union type syntax

### Changed
- Cleaned up 63 stale branches across repositories
- Established `master`/`develop` branch workflow

### Infrastructure
- Docker image published to `b1ackswan/btctx:latest`
- All repositories synced (BitcoinTX-org, PlebRick backup)

---

## [Pre-2025] - Initial Development

### Features
- Double-entry accounting system for BTC transactions
- FIFO cost basis tracking with BitcoinLot/LotDisposal models
- IRS Form 8949 and Schedule D PDF generation
- Dashboard with holdings, balances, and gains
- Transaction entry form (Deposit, Withdraw, Transfer, Buy, Sell)
- Historical BTC price fetching (CoinGecko, Kraken, CoinDesk)
- Session-based authentication
- CSV/PDF transaction history export
