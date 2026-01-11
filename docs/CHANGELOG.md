# Changelog

All notable changes to BitcoinTX are documented in this file.

## [Unreleased]

_Nothing yet_

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

### Changed
- `map_8949_rows_to_field_data()` now accepts `year` parameter for correct field naming
- `map_schedule_d_fields()` now accepts `year` parameter
- `fill_8949_multi_page()` now accepts `year` parameter
- `_verify_templates_exist()` now validates year-specific template availability
- IRS reports endpoint returns helpful error for unsupported years

### Technical Details
- 2024 Form 8949: `Table_Line1`, fields `f1_3` (not zero-padded)
- 2025 Form 8949: `Table_Line1_Part1`/`Part2`, fields `f1_03` (zero-padded for row 1)
- 2024 Schedule D: Short-term uses `f1_07` (zero-padded)
- 2025 Schedule D: Short-term uses `f1_7` (NOT zero-padded)

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
