
# BitcoinTX – Bitcoin Portfolio & Tax Tracker

**BitcoinTX** is a free, open-source Bitcoin portfolio tracker and tax report generator.

It tracks your BTC and USD balances using **double-entry accounting** and helps you calculate FIFO-based capital gains, cost basis, and income for IRS reporting. It includes a full-featured dashboard, a manual transaction entry form, and exportable reports like Form 8949 and Schedule D.

---

## 🧠 Project Goals

- ✅ Track every Bitcoin transaction manually (no exchange sync)
- ✅ Use **FIFO** for cost basis tracking
- ✅ Produce IRS-compliant reports (PDF or CSV)
- ✅ Give you full control and visibility — **self-hosted**
- ✅ Educate new developers with clear architecture and documentation

---

## 🌐 Live Tech Stack

| Layer        | Tech                                  |
| ------------ | ------------------------------------- |
| Frontend     | React + TypeScript + Tailwind + Vite  |
| Backend      | FastAPI + SQLAlchemy + SQLite         |
| Dev Tools    | Conda + VSCode DevContainer + Docker  |
| Report Tools | pandas, WeasyPrint, PyPDF2, Jinja2    |
| Bitcoin API  | Kraken (primary), CoinGecko, CoinDesk |

---

## ✨ Features

- 📈 **Dashboard**: BTC holdings, USD balance, realized/unrealized gains
- 🧾 **Transaction Form**: Deposits, Withdrawals, Transfers, Buys, Sells
- 💼 **Double-Entry Ledger**: Every transaction creates linked debit/credit lines
- 🪙 **BTC Lots & FIFO Tracking**: Acquired BTC is consumed in order
- 📊 **Reports**: Tax reports, cost basis summaries, income history
- 🧮 **BTC Tools**: Calculator and converter with historical BTC price support
- 🔐 **Session-based Auth**: Login system for single user with hashed password

---

## 🚀 Quick Start

> 📘 See [`SETUP_GUIDE.md`](./SETUP_GUIDE.md) for step-by-step instructions.

```bash
# Clone the repo
git clone https://github.com/yourname/BitcoinTX.git
cd BitcoinTX

# Set up Conda and frontend
conda activate btctx-env
conda env update -f environment.yml
cd frontend && npm install

# Create DB & start backend
cd ..
python backend/create_db.py
uvicorn backend.main:app --reload

# In new terminal
cd frontend && npm run dev
```
