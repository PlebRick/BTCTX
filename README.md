## BitcoinTX

---

## Project Goal

BitcoinTX aims to provide a  **single-user** , self-hosted Bitcoin portfolio tracker with  **double-entry accounting** , ensuring accurate transaction logging, real-time cost basis calculations, and seamless tax reporting (e.g., IRS Forms 1040 Schedule D, 8949). The goal is to **transition** from a single-entry system to a more robust **double-entry ledger** that captures both “from” and “to” accounts for every transaction, guaranteeing data integrity and compliance with professional accounting standards.

---

## Technology Stack

### Languages

* **Python** : Primary backend language (FastAPI, SQLAlchemy).
* **TypeScript** : Frontend development within React.
* **JavaScript** : Underlying runtime for Node, used by development tools.

### Frameworks & Libraries

* **FastAPI** : Backend web framework for Python, handling API routes and business logic.
* **SQLAlchemy** : ORM for database interactions (SQLite for storage).
* **React** : Frontend library for building the user interface.
* **React Hook Form** : Library for managing form state and validation on the frontend.
* **bcrypt** : For password hashing (single-user authentication).
* **JWT** : (Planned) JSON Web Tokens for session management.

### Tools

* **VSCode** : Commonly used code editor.
* **Git & GitHub** : Version control, repository hosting, branches (e.g., `main`, feature branches).
* **Docker** : (Planned) For containerizing the backend and frontend if required.
* **pytest** : For Python test automation on the backend.

### Hosting

* **GitHub** : Repository hosting, Issues tracking, Pull Requests, etc.
* **Branches** :
* `master`:
* `dev` or feature branches: In-progress features (e.g., double-entry refactor).

---

## Architecture Overview

### System Architecture

* **Single-Service Backend** (FastAPI) communicating with a **React** frontend.
* **SQLite** database file (`bitcoin_tracker.db`) for persistent storage.
* Plans to adopt a **double-entry** ledger approach: each transaction results in two matching entries (credit/debit) for consistent account balances.

### Key Components

1. **Backend**
   * **Models** (SQLAlchemy): `Transaction`, `Account`, `User`.
   * **Routers** (FastAPI): Endpoints for transactions, accounts, users.
   * **Services** : Business logic (e.g., cost basis calculation, locking).
2. **Frontend**
   * **React App** : Single-page application with multiple pages (Dashboard, Transactions, Reports, Settings).
   * **TransactionForm** : A dynamic form that adapts to transaction type and will eventually handle double-entry fields.
3. **Database**
   * **SQLite** : Currently stores user, account, and transaction data. Moving toward double-entry to ensure accurate logging.

### Data Flow

1. **User Interaction** : The user accesses the React frontend via a browser.
2. **Form Submissions** : Transaction data is POSTed to FastAPI.
3. **Double-Entry Creation** (In Progress): Backend receives data, creates two entries (debit/credit) to reflect the transfer of funds across accounts.
4. **Data Persistence** : SQLAlchemy commits changes to SQLite.
5. **Response** : The backend returns updated records or success messages to the frontend.

---

## Current State of Development

### Development Phase

Currently in an **active development** phase, transitioning from a minimal single-entry MVP to a more **professional double-entry** system.

### Completed Features

* **Basic CRUD** for Transactions, Accounts, Users in FastAPI.
* **Dynamic Transaction Form** on the frontend (handles deposits, withdrawals, transfers, buys, sells).
* **CORS Configuration** to allow local React → FastAPI calls.
* **Basic Cost Basis Fields** : `cost_basis_usd` tracked for BTC inflows.
* **Year-End Lock Placeholder** : An `is_locked` flag prepared for locking old transactions.

### Pending Features

* **Full Double-Entry Implementation** : Shifting from single to double-transaction records for Transfers (and eventually for all transaction types).
* **Robust Cost Basis** : Implementing FIFO logic for realized/unrealized gains, partial-lot sales, etc.
* **Year-End Lock Mechanism** : Marking a date, after which no edits occur for that year’s transactions.
* **Advanced Reporting** : Summaries for tax returns (e.g., short/long-term gains, Form 8949 exports).

---

## Testing Environment

### Backend Testing

* **Pytest** used with **TestClient** (FastAPI test utilities).
* FastAPI SwaggerUI
* Local environment runs on `127.0.0.1:8000` with a test database or ephemeral in-memory DB.

### Frontend Testing

* **React Testing Library** or other testing frameworks (planned).
* Local environment typically runs on `127.0.0.1:5173` via  **Vite** .

### Integration Tests

* Currently minimal. Planned to expand once the double-entry logic is stable (e.g., verifying a Transfer is reflected in both “from” and “to” accounts).

---

## Project Challenges

### Known Issues

* **Transfer Gaps** : Single-entry transfers omit the destination account ledger, leading to incorrect or incomplete balances.
* **Locking** : `is_locked` logic not fully enforced. Changing locked transactions can break cost basis flow.

### Technical Challenges

* **Double-Entry Refactor** : Potentially large schema changes, ensuring two transaction records for each “transfer” event, and possibly for other transaction types.
* **Complex FIFO** : Handling partial-lot sales or merges from multiple deposit events.
* **User Experience** : Balancing the complexity of double-entry forms with user-friendly design.

---

## Documentation

### Location

* **README** files in the project root and `backend/`.
* **TODO.md** in the project root for short-term tasks.


---

## Future Roadmap

### Short-Term Goals

* **Implement Double-Entry** : Refactor Transfer logic so each transaction stores both debit and credit entries.
* **Refine TransactionForm** : Ensure the UI can handle new double-entry fields gracefully, especially for Transfers.
* **Improve Test Coverage** : Write more integration tests to confirm that double-entry data flows properly.

### Long-Term Vision

* **Complete Tax Reporting** : Produce forms 1040 Schedule D, 8949, or at least detailed CSV exports.
* **Year-End Archiving** : Lock and possibly compress data from prior years for performance.
* **User Experience Enhancements** : Possibly add multi-user support, 2FA, or advanced analytics dashboards.
* **Broad Deployability** : Containerization with Docker, plus packaging for self-hosting solutions like Start9's StartOS

---

## Miscellaneous

* **Branching Strategy** : Merges into `main` after feature branches are tested.
* **Versioning** : Basic semantic versioning (in future).
* **Security** : Single-user approach, but best practices in encryption, password hashing, and limited external surface area.

---
