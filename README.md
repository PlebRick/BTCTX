# BitcoinTX – Bitcoin Portfolio & Tax Tracker

**BitcoinTX** is a free, open-source Bitcoin portfolio tracker and tax report generator.

It tracks your BTC and USD balances using **double-entry accounting** and helps you calculate FIFO-based capital gains, cost basis, and income for IRS reporting. It includes a full-featured dashboard, a manual transaction entry form, and exportable reports like Form 8949 and Schedule D.

<img width="1388" alt="image" src="https://github.com/user-attachments/assets/3adf19f4-28e1-462d-8318-ccb35f6ca576" />

<img width="1490" alt="image" src="https://github.com/user-attachments/assets/597e6709-2638-433e-9a54-2e7c70d082da" />

<img width="955" alt="image" src="https://github.com/user-attachments/assets/8316fa63-4af9-4f2d-af03-bb3e7cbc5633" />

---

## Project Goals

- ✅ Track every Bitcoin transaction manually (no exchange sync)
- ✅ Use **FIFO** for cost basis tracking
- ✅ Produce IRS-compliant reports (PDF or CSV)
- ✅ Give you full control and visibility — **self-hosted**
- ✅ Educate new developers with clear architecture and documentation

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
