# CLAUDE.md - AI Assistant Context File

> This file provides context for AI assistants (Claude, etc.) working on this project.
> It should be updated after significant changes to maintain continuity across sessions.

**Last Updated:** 2025-01-16

---

## IMPORTANT: Check Current Branch First

**At the start of every new session, check what branch you're on and what work is in progress:**

```bash
git branch          # See current branch
git status          # See uncommitted changes
git log -3 --oneline  # See recent commits
```

### Branch Workflow

| Branch | Purpose | When to Use |
|--------|---------|-------------|
| `develop` | Stable development | Normal bug fixes, small changes |
| `feature/*` | Major changes | Risky/complex work (e.g., `feature/2025-forms`) |
| `master` | Production releases | Only merge from develop when stable |

### Active Feature Branches

None currently. All feature branches have been merged and deleted.

### Feature Branch Rules

1. **Create feature branch for major work:**
   ```bash
   git checkout develop
   git checkout -b feature/my-feature
   ```

2. **When feature is complete and tested:**
   ```bash
   git checkout develop
   git merge feature/my-feature
   git branch -d feature/my-feature  # Delete local
   git push origin --delete feature/my-feature  # Delete remote
   ```

3. **Keep feature branch updated with develop:**
   ```bash
   git checkout feature/my-feature
   git merge develop  # Pull in any bug fixes from develop
   ```

- Never commit directly to `master`
- Use feature branches for major/risky changes

---

## Key Architectural Decisions

### Multi-Year IRS Form Support

**Decision:** The app maintains all historical IRS form templates in a year-based folder structure. This allows users to generate reports for any supported tax year without needing old app versions.

```
backend/assets/irs_templates/
├── 2024/
│   ├── f8949.pdf
│   └── f1040sd.pdf
├── 2025/
│   └── ...
```

**Rationale:**
- Users may need to file amended/late returns for prior years
- Single codebase is simpler than maintaining multiple app versions
- New tax year = add folder + update field mappings if changed

**Versioning:** Bump minor version when adding new tax year forms (e.g., v0.3.0 for 2025 forms).

See [docs/IRS_FORM_GENERATION.md](docs/IRS_FORM_GENERATION.md) for complete details.

---

## Project Overview

BitcoinTX is a self-hosted Bitcoin portfolio tracker with IRS tax form generation capabilities.

### Architecture

```
Single Docker Container
├── Backend: FastAPI (Python 3.11) on Uvicorn
│   ├── API endpoints at /api/*
│   ├── SQLite database at /data/btctx.db
│   └── PDF generation with pdftk
└── Frontend: React/Vite (static files served at /*)
```

### Core Data Model

```
Transaction (user input)
    ↓ creates
LedgerEntry (double-entry: debit + credit)
    ↓ for BTC acquisitions, creates
BitcoinLot (cost basis tracking)
    ↓ when BTC is sold/spent, creates
LotDisposal (FIFO consumption record)
```

### Key Files

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI app entry point, mounts routers |
| `backend/database.py` | SQLite setup, `get_db()` dependency |
| `backend/models/` | SQLAlchemy models (Transaction, LedgerEntry, BitcoinLot, etc.) |
| `backend/services/transaction.py` | Transaction processing, FIFO logic |
| `backend/services/bitcoin.py` | BTC price fetching (CoinGecko, Kraken, CoinDesk) |
| `backend/routers/reports.py` | PDF report generation endpoints |
| `backend/services/reports/form_8949.py` | IRS Form 8949 data preparation |
| `Dockerfile` | Multi-stage build (Node for frontend, Python for backend) |

---

## Current State

### What's Working
- All transaction types (Deposit, Withdraw, Transfer, Buy, Sell)
- Double-entry ledger with proper debit/credit
- FIFO cost basis tracking
- IRS Form 8949 + Schedule D generation (pdftk)
- Complete tax report (ReportLab)
- Transaction history export (CSV/PDF)
- Docker deployment on port 80
- BTC price fetching with 3-source fallback

### Docker Image
- **Registry:** Docker Hub
- **Image:** `b1ackswan/btctx:latest`
- **Port:** 80
- **Data Volume:** `/data` (SQLite database)
- **Architectures:** `linux/amd64`, `linux/arm64` (multi-arch)

> **CRITICAL:** Before modifying ANY code that touches database paths, file storage, or environment variables, you MUST read [docs/STARTOS_COMPATIBILITY.md](docs/STARTOS_COMPATIBILITY.md). This document explains how data persistence works in Docker/StartOS containers and documents past bugs caused by hardcoded paths.

### Git State
- **Primary Repo:** BitcoinTX-org/BTCTX (origin)
- **Backup Repo:** PlebRick/BTCTX (plebrick remote)
- **Branches:** `master` (production), `develop` (active work)

---

## Git Workflow & Versioning

### Remotes
| Remote | Repo | Push Frequency |
|--------|------|----------------|
| `origin` | BitcoinTX-org/BTCTX | Every commit during development |
| `plebrick` | PlebRick/BTCTX | **Only at stable milestones/releases** |

**IMPORTANT:** Do NOT push to `plebrick` automatically. Only sync when explicitly requested or at tagged releases.

### Branches
- `develop` - Active development, push here regularly
- `master` - Production-ready code, merge from develop when stable

### Tags & Releases
Use semantic versioning: `vMAJOR.MINOR.PATCH`
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

```bash
# Create a release
git checkout master
git merge develop
git tag -a v1.0.0 -m "Release v1.0.0: Description"
git push origin master --tags
git push plebrick master --tags  # Sync backup at releases
```

### Current Version
- **Latest Tag:** `v0.5.1` (2025-01-15)
- **Status:** Stable release with FIFO account-specific fix, test fixes, logo updates
- **Docker Image:** `b1ackswan/btctx:v0.5.1` (also `latest`)
- **Target Release:** `v1.0.0`

---

## Recent Changes (Jan 2025)

### Session: 2025-01-16
1. **CSV Template Fix**
   - Fixed broken template that had incorrect balance math (withdrawals exceeded deposits)
   - New template has 18 transactions (was 7) with verified balance math
   - Includes all transaction types: Deposit, Withdrawal, Transfer, Buy, Sell
   - Includes all deposit sources: MyBTC, Gift, Income, Interest, Reward
   - Includes all withdrawal purposes: Spent, Gift, Donation, Lost
   - File: `backend/services/csv_import.py`

2. **CSV Import Ordering Fix**
   - Added same-timestamp sorting: acquisitions (Deposit, Buy) process before disposals (Sell, Withdrawal)
   - Fixes edge case where same-timestamp transactions could fail due to ordering
   - File: `backend/services/csv_import.py`

3. **CSV Export Ordering Fix**
   - Added deterministic ordering by ID for same-timestamp transactions
   - Ensures consistent export order across runs
   - File: `backend/routers/backup.py`

4. **Docker Image Update**
   - Rebuilt with `--no-cache` and pushed to Docker Hub
   - Tags: `b1ackswan/btctx:v0.5.1`, `b1ackswan/btctx:latest`

### Session: 2025-01-15
1. **FIFO Lot Disposal Fix**
   - Made FIFO disposal account-specific (was consuming lots from all accounts globally)
   - File: `backend/services/transaction.py`

2. **Test Fixes**
   - Fixed 5 stale tests to match current codebase
   - All 84 tests now pass
   - Files: `test_backend.py`, `test_main.py`, `test_seed_data_integrity.py`

3. **SPA Routing Fix (Docker)**
   - Fixed browser refresh returning 404 JSON on client-side routes (`/dashboard`, `/transactions`, etc.)
   - Root cause: `StaticFiles(html=True)` does NOT provide SPA fallback for arbitrary paths
   - Solution: Added `spa_fallback_handler` exception handler to serve `index.html` for non-API 404s
   - API routes still return proper JSON errors (`{"detail":"Not Found"}`)
   - File: `backend/main.py`

4. **UI Fixes**
   - Fixed Toast close button not rendering (Unicode escape issue)
   - Updated application logo (`logo.svg`, `icon.svg`)
   - Removed unused `bitcoin-logo.png`

4. **Release v0.5.1**
   - Tagged and pushed to both repos (origin, plebrick)
   - Built and pushed multi-arch Docker image

### Session: 2025-01-10
1. **Python 3.9 Compatibility**
   - Added `from __future__ import annotations` to `transaction.py` and `user.py`
   - Fixes union type syntax (`datetime | None` → works on Python 3.9)

2. **PDF Path Fixes**
   - Changed relative paths to absolute paths using `__file__`
   - Added pre-flight checks (`_verify_pdftk_installed()`, `_verify_templates_exist()`)
   - File: `backend/routers/reports.py`

3. **Docker BTC Price Fix**
   - Changed `get_btc_price()` from HTTP calls to direct service calls
   - Was calling `localhost:8000` but Docker runs on port 80
   - File: `backend/services/transaction.py`

4. **Repository Cleanup**
   - Deleted 63 stale branches across repos
   - Established master/develop workflow

---

## Known Issues & Future Work

### Deferred Items
- [x] ~~Edge cases in FIFO calculations~~ (covered by pre-commit tests)
- [x] ~~Review PDF calculations for accuracy~~ (verified, fixed Form 8949 non-taxable exclusion)
- [ ] 2025 IRS form template updates (when released)

### Planned Features
- [ ] Multi-user support (optional)
- [ ] CSV import merge with existing data (Phase 2)

### Completed Recently
- [x] Frontend design system refactor (Jan 2025)
  - Custom hooks: `useAccounts`, `useApiCall`, `useBtcPrice`
  - Toast notification system with context
  - Error boundaries for graceful error handling
  - Centralized theme system (`theme.css`)
- [x] CSV template import feature (v0.4.0)
- [x] Atomic bulk import with rollback
- [x] Pre-commit test suite (17 tests)
- [x] Fixed Form 8949 to exclude Gift/Donation/Lost disposals

---

## Development Notes

### Running Locally
```bash
# Backend
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000

# Frontend (dev mode)
cd frontend && npm run dev

# Frontend (production build)
cd frontend && npm run build
# Then backend serves static files from frontend/dist
```

### Running in Docker
```bash
# Local single-arch build
docker build -t btctx .
docker run -p 80:80 -v btctx-data:/data btctx

# Multi-arch build for production (required for StartOS compatibility)
docker buildx build --platform linux/amd64,linux/arm64 \
  -t b1ackswan/btctx:latest --push .
```

> See [docs/STARTOS_COMPATIBILITY.md](docs/STARTOS_COMPATIBILITY.md) for full multi-arch build requirements.

### Pre-Commit Testing (IMPORTANT)

**Run the pre-commit test suite before every commit**, especially when modifying backend code:

```bash
# Full test suite (starts backend if needed)
./scripts/pre-commit.sh

# Quick mode (skip long-running tests)
./scripts/pre-commit.sh --quick

# Static checks only (no backend needed)
python3 backend/tests/pre_commit_tests.py --no-api
```

**What it tests (17 checks):**
- Docker/StartOS compatibility (no hardcoded paths, DATABASE_FILE env var, Python 3.9)
- Transaction/FIFO integrity (scorched earth recalculation, backdated transactions)
- Report generation (Form 8949, Schedule D, non-taxable exclusions)
- CSV import/export roundtrip

**Critical files that REQUIRE pre-commit tests after changes:**
- `backend/services/transaction.py` - FIFO logic, lot disposal
- `backend/services/reports/form_8949.py` - Tax form generation
- `backend/database.py` - Database paths
- `backend/services/backup.py` - Backup/restore paths
- Any file touching file paths or environment variables

### Testing Reports
```bash
# Complete tax report
curl "http://localhost:8000/api/reports/complete_tax_report?year=2024" -o report.pdf

# IRS forms (requires pdftk)
curl "http://localhost:8000/api/reports/irs_reports?year=2024" -o irs.pdf

# Transaction history
curl "http://localhost:8000/api/reports/simple_transaction_history?year=2024&format=csv" -o history.csv
```

### Key Dependencies
- `pdftk` - Required for IRS form filling (install via brew/apt)
- `pypdf` - PDF merging
- `reportlab` - PDF generation from scratch
- `httpx` - Async HTTP for price APIs

---

## Handoff Checklist

When starting a new session, the AI should:
1. Read this file first (`CLAUDE.md` - auto-detected in root)
2. Check `docs/CHANGELOG.md` for recent changes
3. Check `docs/ROADMAP.md` for current goals
4. **Before any database/storage/Docker changes:** Review `docs/STARTOS_COMPATIBILITY.md` - this is CRITICAL for understanding how data persistence works
5. **Before updating dependencies:** Review `docs/MAINTENANCE.md` for safe update procedures and known issues
6. Run `git status` to see uncommitted changes
7. Run `git log -5 --oneline` to see recent commits

When ending a session:
1. **Run pre-commit tests:** `./scripts/pre-commit.sh` (or `--no-api` for quick check)
2. Update this file with any significant changes
3. Add entries to CHANGELOG.md
4. Update ROADMAP.md if goals changed
5. If dependencies were updated, update `docs/MAINTENANCE.md` with any new deprecation warnings
6. Commit changes if appropriate
