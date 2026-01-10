# CLAUDE.md - AI Assistant Context File

> This file provides context for AI assistants (Claude, etc.) working on this project.
> It should be updated after significant changes to maintain continuity across sessions.

**Last Updated:** 2025-01-10

---

## IMPORTANT: Always Start on `develop` Branch

**At the start of every new session, ALWAYS checkout the `develop` branch before making any changes:**

```bash
git checkout develop
git pull origin develop
```

- All development work happens on `develop`
- Only merge to `master` for releases
- Never commit directly to `master`

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

> **IMPORTANT:** See [docs/STARTOS_COMPATIBILITY.md](docs/STARTOS_COMPATIBILITY.md) for critical requirements that must be maintained for StartOS packaging compatibility.

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
- **Latest Tag:** `v0.2.0-beta` (2025-01-10)
- **Status:** StartOS packaging complete, entering beta testing
- **Target Release:** `v1.0.0`

---

## Recent Changes (Jan 2025)

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
- [ ] Edge cases in FIFO calculations
- [ ] Review PDF calculations for accuracy
- [ ] 2025 IRS form template updates (when released)

### Planned Features
- [ ] CSV import for bulk transactions
- [ ] Multi-user support (optional)

### Completed This Session
- [x] StartOS packaging (tested `.s9pk` working)
- [x] Backdated transaction FIFO recalculation
- [x] Lost BTC capital loss tax treatment
- [x] Insufficient BTC validation
- [x] UI responsiveness improvements

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
4. **Before any Docker/Dockerfile changes:** Review `docs/STARTOS_COMPATIBILITY.md`
5. Run `git status` to see uncommitted changes
6. Run `git log -5 --oneline` to see recent commits

When ending a session:
1. Update this file with any significant changes
2. Add entries to CHANGELOG.md
3. Update ROADMAP.md if goals changed
4. Commit changes if appropriate
