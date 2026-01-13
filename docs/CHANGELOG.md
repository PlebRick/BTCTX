# Changelog

All notable changes to BitcoinTX are documented in this file.

## [Unreleased]

### Added
- **CSV Export**: Export all transactions as a CSV file matching the import template format
  - Creates clean roundtrip: Export → Edit → Re-import
  - File naming: `btctx_transactions_YYYY-MM-DD.csv`
  - New endpoint: `GET /api/backup/csv`
- **CSV Import Instructions PDF**: Downloadable PDF guide for CSV import feature
  - Comprehensive field reference with valid values
  - Account rules by transaction type
  - Example rows for each transaction type
  - Troubleshooting guide
  - New endpoint: `GET /api/import/instructions`
- **Frontend buttons in Settings**:
  - "Instructions" button next to CSV import template download
  - "Export CSV" button in Backup & Restore section
- **Pre-Commit Test Suite**: Comprehensive test battery for catching regressions
  - Docker/StartOS compatibility checks (hardcoded paths, env vars, Python 3.9)
  - Transaction/FIFO integrity tests (scorched earth, backdated recalculation)
  - Report generation tests (Form 8949, Schedule D, Complete Tax Report)
  - CSV import/export roundtrip validation
  - Run with: `./scripts/pre-commit.sh` or `python backend/tests/pre_commit_tests.py`

### Fixed
- **Form 8949 non-taxable exclusion**: Gift, Donation, and Lost disposals now correctly excluded from IRS Form 8949
  - Added `NON_TAXABLE_PURPOSES` filter in `form_8949.py`
  - These disposal types should not appear on tax forms per IRS guidelines
- **Proceeds degradation fix**: Fixed bug where `proceeds_usd` could degrade during recalculation
  - `maybe_dispose_lots_fifo` now uses authoritative `tx.proceeds_usd` instead of stale `tx_data`
- **CSV export roundtrip**: Export now correctly outputs user-entered values only
  - `cost_basis_usd` exported only for Buy/Deposit transactions
  - `gross_proceeds_usd` used for Sell/Withdrawal (not FIFO-calculated values)

### Files Added
- `backend/scripts/generate_csv_instructions_pdf.py` - ReportLab script to generate instructions PDF
- `backend/assets/csv_import_instructions.pdf` - Static PDF with import instructions
- `backend/tests/pre_commit_tests.py` - Comprehensive pre-commit test suite
- `scripts/pre-commit.sh` - Shell script wrapper for pre-commit tests

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
