# BitcoinTX – Bitcoin Portfolio & Tax Tracker

**BitcoinTX** is a free, open-source Bitcoin portfolio tracker and tax report generator.

It tracks your BTC and USD balances using **double-entry accounting** and helps you calculate FIFO-based capital gains, cost basis, and income for IRS reporting. It includes a full-featured dashboard, a manual transaction entry form, and exportable reports like Form 8949 and Schedule D.

<img width="1000" alt="Dashboard" src="docs/images/dashboard.png" />

<img width="1000" alt="Transactions" src="docs/images/transactions.png" />

<img width="1000" alt="Reports" src="docs/images/reports.png" />

<img width="1000" alt="Settings" src="docs/images/settings.png" />

---

## Project Goals

- Track every Bitcoin transaction manually (no exchange sync)
- Use **FIFO** for cost basis tracking
- Produce IRS-compliant reports (PDF or CSV)
- Full control and visibility — **self-hosted**
- Clear architecture and documentation for developers

---

## Tech Stack

| Layer        | Tech                                      |
| ------------ | ----------------------------------------- |
| Frontend     | React + TypeScript + Vite                 |
| Backend      | FastAPI + SQLAlchemy + SQLite             |
| Deployment   | Docker (single container)                 |
| Report Tools | pdftk, pypdf, ReportLab                   |
| Bitcoin API  | CoinGecko (primary), Kraken, CoinDesk     |

---

## Features

- **Dashboard**: BTC holdings, USD balance, realized/unrealized gains
- **Transaction Form**: Deposits, Withdrawals, Transfers, Buys, Sells
- **Double-Entry Ledger**: Every transaction creates linked debit/credit lines
- **BTC Lots & FIFO Tracking**: Acquired BTC is consumed in order
- **Reports**: IRS Form 8949, Schedule D, tax summaries, transaction history (PDF/CSV)
- **BTC Tools**: Calculator and converter with historical BTC price support
- **Session-based Auth**: Login system for single user with hashed password

---

## Quick Start

### Docker (Recommended)

```bash
# Pull and run
docker pull b1ackswan/btctx:latest
docker run -d -p 80:80 -v btctx-data:/data b1ackswan/btctx:latest

# Open http://localhost in your browser
```

### Local Development

```bash
# Clone the repo
git clone https://github.com/BitcoinTX-org/BTCTX.git
cd BTCTX

# Backend setup (Python 3.9+)
cp .env.example .env
pip install -r backend/requirements.txt

# Frontend setup
cd frontend && npm install && npm run build && cd ..

# Run
uvicorn backend.main:app --reload --port 8000
# Open http://localhost:8000
```

### Requirements

- **Python 3.9+** (3.11 recommended)
- **Node.js 18+** (for frontend build)
- **pdftk** (for IRS form generation)
  - macOS: `brew install pdftk-java`
  - Linux: `apt-get install pdftk`
