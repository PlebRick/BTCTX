# BitcoinTX – Bitcoin Portfolio & Tax Tracker

**BitcoinTX** is a single-user, self-hosted Bitcoin portfolio tracker with a double-entry accounting approach. It ensures every transaction is recorded on both sides of the ledger (debit and credit) for accurate balances, real-time cost basis tracking, and seamless tax reporting integration ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=BitcoinTX%20aims%20to%20provide%20a,compliance%20with%20professional%20accounting%20standards)). The project is in active development, having recently refactored from a simple single-entry MVP to a  **hybrid double-entry system** . In this hybrid model, internal transfers now generate two linked entries (one to debit the source account and one to credit the destination) to maintain a balanced ledger. The ultimate goal is to fully transition to a robust double-entry ledger capturing both “from” and “to” accounts for every transaction ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=cost%20basis%20calculations%2C%20and%20seamless,compliance%20with%20professional%20accounting%20standards)), ensuring data integrity and compliance with professional accounting standards.

---

## Technology Stack

### Languages

* **Python** – Primary backend language (FastAPI, SQLAlchemy).
* **TypeScript** – Frontend language (React with Vite).
* **JavaScript** – Used by build tools and scripts (Node runtime).

### Frameworks & Libraries

* **FastAPI** – Backend web framework (handles API routes and business logic).
* **SQLAlchemy** – ORM for database interactions (using SQLite for storage).
* **React** – Frontend library for building the user interface.
* **React Hook Form** – Manages form state and validation on the frontend.
* **bcrypt** – Password hashing for the single-user authentication.
* **JWT** – *(Planned)* JSON Web Tokens for session management and API auth.

### Tools

* **VSCode** – Commonly used code editor.
* **Git & GitHub** – Version control and repo hosting (using branches like `master` for stable and feature branches for development).
* **Docker** – *(Planned)* Containerization for easier deployment of backend and frontend.
* **Pytest** – Used for backend test automation.

### Hosting

* **GitHub** – Repository hosting, issue tracking, and pull requests.
* **Branching** –
  * `master` – Main branch for stable code.
  * `dev` or feature branches – In-progress features (e.g. the double-entry refactor) ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=,entry%20refactor)).

---

## Architecture Overview

### System Architecture

* **Backend** – Single service (FastAPI) providing a RESTful API.
* **Frontend** – React single-page app (SPA) served separately (dev server via Vite).
* **Database** – SQLite file (`bitcoin_tracker.db`) for persistent storage.

The application is adopting a double-entry ledger approach: each transaction ideally results in two matching entries (credit and debit) for consistent account balances ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=%2A%20Single,for%20consistent%20account%20balances)). *(Currently, this is implemented for transfer transactions, with other transaction types to be migrated.)*

### Key Components

1. **Backend** :

* *Models* – SQLAlchemy models such as `User`, `Account`, and `Transaction` (to be extended for double-entry).
* *Routers* – FastAPI routers for handling endpoints (transactions, accounts, users).
* *Services* – Business logic (e.g. cost basis calculation, year-end locking) ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=,Frontend)).

1. **Frontend** :

* *React App* – Provides a UI with pages for Dashboard, Transactions, Reports, Settings.
* *Transaction Form* – Dynamic form for adding/editing transactions (supports deposits, withdrawals, transfers, buys, sells). This form will be updated to handle double-entry fields as the backend evolves ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=%2A%20React%20App%20%3A%20Single,entry%20to%20ensure%20accurate%20logging)).

1. **Database** :

* *SQLite* – Stores users, accounts, and transactions. The schema is in transition toward double-entry to ensure accurate logging of all sides of a transaction ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=3.%20Database%20,entry%20to%20ensure%20accurate%20logging)).

### Data Flow

1. **User Interaction** – The user operates the React frontend in a browser.
2. **Form Submission** – Transaction data (e.g. a new transaction) is sent via HTTP POST to the FastAPI backend.
3. **Double-Entry Creation** – For transfer transactions, the backend creates two entries (debit and credit) to reflect the movement of funds between the source and destination accounts ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=1,success%20messages%20to%20the%20frontend)). (Other transaction types currently still create a single entry until the double-entry refactoring is complete.)
4. **Data Persistence** – SQLAlchemy ORM commits the new transaction entries to the SQLite database.
5. **Response** – The backend returns the created record(s) or a success status, and the frontend updates the UI accordingly.

---

## Current State of Development

### Development Phase

The project is in an **active development** phase. A recent refactor introduced partial double-entry support (hybrid system), and the application is evolving from a basic single-entry MVP to a more robust double-entry architecture. Development is rapid, with frequent commits focused on implementing core features and improving stability.

### Completed Features

* **Basic CRUD Operations** – Create, read, update, delete functionality for Transactions, Accounts, and the single User via FastAPI.
* **Dynamic Transaction Form** – Frontend form that adapts to different transaction types (deposit, withdrawal, transfer, buy, sell).
* **CORS Configured** – Backend configured with CORS to allow the React frontend (usually running on a different port) to communicate with the API.
* **Cost Basis Field** – Basic cost basis tracking: a `cost_basis_usd` field is recorded for BTC inflow transactions (to capture the USD value at the time of acquisition) ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=match%20at%20L308%20,prepared%20for%20locking%20old%20transactions)).
* **Year-End Lock Flag** – An `is_locked` flag exists on transactions as a placeholder for a future feature that will lock transactions from editing after a certain date (e.g. end of year) ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=,prepared%20for%20locking%20old%20transactions)).
* **Hybrid Double-Entry for Transfers** – *New:* Internal transfers now generate two transaction entries under the hood (one debiting the source account and one crediting the destination account) to ensure both accounts’ balances update correctly, fulfilling the double-entry requirement for transfer events ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=1,success%20messages%20to%20the%20frontend)). This fixes prior balance discrepancies for transfers.

### Pending Features

* **Extend Double-Entry to All Transactions** – Continue expanding the double-entry system. Currently only transfers are fully double-entry; the goal is to have all transaction types (buys, sells, deposits, withdrawals) recorded with corresponding debit/credit entries or linked journal records for complete consistency ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=%2A%20Implement%20Double,fields%20gracefully%2C%20especially%20for%20Transfers)). This may involve schema changes (e.g. introducing a journal table or linking transactions) and thorough data migration.
* **Robust Cost Basis Calculation** – Implement FIFO-based cost basis and tracking of lots for more accurate realized and unrealized gain/loss calculations ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=,occur%20for%20that%20year%E2%80%99s%20transactions)). For example, when a portion of BTC is sold, the system should determine which purchase lots to attribute to the sale (handling partial lot sales) and calculate gains accordingly.
* **Year-End Lock Mechanism** – Fully enforce the year-end locking feature ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=,occur%20for%20that%20year%E2%80%99s%20transactions)). Once a year (or user-specified date) is closed out, transactions before that cutoff date should be immutable (read-only) to prevent retroactive changes that would affect reported totals. This includes UI indicators for locked entries and backend validation to reject edits on locked records.
* **Advanced Reporting** – Develop reporting features for tax and portfolio purposes. This includes summaries of short-term vs long-term capital gains, generation of IRS forms (like Schedule D and Form 8949) or at least CSV exports of transactions categorized by gains/losses ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=%2A%20Full%20Double,term%20gains%2C%20Form%208949%20exports)). These reports will use the enhanced cost basis calculations and double-entry data to ensure accuracy.

---

## Testing Environment

### Backend Testing

* **Pytest** – Tests are written using Pytest, utilizing FastAPI’s `TestClient` for API endpoint testing ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=Backend%20Testing)).
* **Interactive Docs** – FastAPI’s built-in Swagger UI is available for manual testing of endpoints.
* **Local Development** – The backend runs at `127.0.0.1:8000` (by default) with a local SQLite database (or an in-memory database for tests) ([GitHub - PlebRick/BTCTX: Bitcoin portfolio and capital gains tracker](https://github.com/PlebRick/BTCTX#:~:text=,memory%20DB)).

### Frontend Testing

* **Manual/UI Testing** – During development, the React app (running on `127.0.0.1:5173` via Vite) can be used to manually test interactions ([GitHub - PlebRick/BTCTX: Bitcoin portfolio and capital gains tracker](https://github.com/PlebRick/BTCTX#:~:text=,via%20Vite)). Formal automated tests (e.g. with React Testing Library) are planned but not fully in place yet.
* **Planned Automated Tests** – Future plans include using React Testing Library and Jest to create unit and integration tests for the frontend components and forms.

### Integration Tests

* Currently  **minimal** . As the double-entry functionality stabilizes, more integration tests will be added. For example, a test will ensure that creating a transfer results in two entries and that both the source and destination account balances update correctly ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=match%20at%20L341%20,both%20%E2%80%9Cfrom%E2%80%9D%20and%20%E2%80%9Cto%E2%80%9D%20accounts)). End-to-end tests might also simulate user workflows (adding transactions, viewing reports, etc.) once the core features are in place.

---

## Project Challenges

### Known Issues

* **Partial Double-Entry Implementation** – Until the refactor is complete, not all transactions are double-entry. For instance, a *buy* or *sell* is still recorded as a single entry (affecting only the BTC account). This means the other side of those transactions (e.g. the fiat currency used to buy BTC) isn’t yet tracked in the system, which could lead to incomplete portfolio accounting. This inconsistency will be resolved as the double-entry system is extended to all transaction types.
* **Transaction Locking Not Enforced** – The `is_locked` flag and year-end lock concept are not yet enforced. A user could still modify or delete transactions from past years, which would mess up historical balances and tax calculations ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=,prepared%20for%20locking%20old%20transactions)). This is slated to be addressed when the lock mechanism is implemented.

### Technical Challenges

* **Double-Entry Refactor** – Migrating to double-entry is a significant change. It requires schema updates (potentially splitting a single transaction into multiple records or a new table for journal entries) and careful handling in code to keep entries in sync ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=%2A%20Double,or%20merges%20from%20multiple%20deposit)). Ensuring data integrity (both entries saved or none) and updating all related logic (APIs, forms, calculations) is complex. A migration strategy for existing data is also a concern if any transactions were recorded in the old format.
* **Complex FIFO Calculations** – Implementing accurate FIFO cost basis for partial sales is non-trivial ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=transaction%20types.%20,or%20merges%20from%20multiple%20deposit)). The system must track multiple lots of BTC bought at different times/prices and determine which lots are sold in each transaction. Edge cases like selling more BTC than currently in one lot (requiring splitting lots) or consolidating multiple small purchases into one sale need to be handled.
* **User Experience** – As the system adopts more rigorous accounting rules, the UI must remain user-friendly ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=,friendly%20design)). Double-entry accounting can be confusing to end-users who just want to record a simple trade or transfer. Designing the forms and displays to hide complexity (for example, auto-creating the second leg of a transfer) will be important. Similarly, presenting cost basis and tax info in an understandable way is a UX challenge.

---

## Documentation

### Locations

* **README** – High-level project documentation is provided in this README (project overview, architecture, roadmap, etc.) and in a separate `README.md` within the `backend/` directory (for backend-specific details) ([GitHub - PlebRick/BTCTX: Bitcoin portfolio and capital gains tracker](https://github.com/PlebRick/BTCTX#:~:text=Documentation)).
* **TODO** – Short-term tasks and the development roadmap are tracked in `TODO.md` in the project root ([GitHub - PlebRick/BTCTX: Bitcoin portfolio and capital gains tracker](https://github.com/PlebRick/BTCTX#:~:text=Location)).
* **Code Comments** – The codebase is being commented for clarity where important, especially around complex logic like cost basis calculations and double-entry handling.
* **API Docs** – The FastAPI backend automatically generates interactive API documentation (Swagger UI) at the `/docs` endpoint when running, which can be used as up-to-date reference for available endpoints and data models.

---

## Future Roadmap

### Short-Term Goals

* **Complete Double-Entry Migration** – Finalize the transition to double-entry accounting for all transaction types. This involves refactoring remaining single-entry operations (buys, sells, etc.) so that each transaction has corresponding debit/credit records, and updating the UI and API to support this change ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=%2A%20Implement%20Double,fields%20gracefully%2C%20especially%20for%20Transfers)).
* **Refine Transaction Form** – Update the React frontend forms to gracefully handle the new double-entry data. For transfers, the form should allow selecting both a source and destination account. For other types, consider how to incorporate the second ledger entry (e.g., specifying the opposing account or category) without confusing the user ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=%2A%20Implement%20Double,fields%20gracefully%2C%20especially%20for%20Transfers)).
* **Improve Test Coverage** – As new features (double-entry, FIFO, etc.) are added, expand the test suite. This includes backend tests for accounting logic and frontend tests for the UI, ensuring that critical scenarios (like a transfer updating two accounts) work correctly ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=match%20at%20L341%20,both%20%E2%80%9Cfrom%E2%80%9D%20and%20%E2%80%9Cto%E2%80%9D%20accounts)).

### Long-Term Vision

* **Complete Tax Reporting** – Generate tax documentation or exports from the data. For example, produce a Form 8949 or Schedule D report summarizing capital gains for the year ([GitHub - PlebRick/BTCTX: Bitcoin portfolio and capital gains tracker](https://github.com/PlebRick/BTCTX#:~:text=Long)). Even if official forms are not directly created, the system will at least allow CSV export of all transactions with cost basis and gain/loss calculations for easy import into tax software.
* **Year-End Archiving** – Implement an archiving solution for old data. After a year is locked and completed, the data could be archived or moved to improve performance on the active dataset ([GitHub - PlebRick/BTCTX: Bitcoin portfolio and capital gains tracker](https://github.com/PlebRick/BTCTX#:~:text=,hosting%20solutions%20like%20Start9%27s%20StartOS)). This might include compressing historical transactions or off-loading them to a read-only archive, while keeping summary balances.
* **User Experience Enhancements** – Over time, add features to improve usability and widen the audience: for instance, multi-user support (so more than one person can securely use the app) and two-factor authentication for the login ([GitHub - PlebRick/BTCTX: Bitcoin portfolio and capital gains tracker](https://github.com/PlebRick/BTCTX#:~:text=%2A%20Year,2FA%2C%20or%20advanced%20analytics%20dashboards)). Additionally, build more advanced analytics dashboards (e.g. charts of portfolio value over time, allocation by account) to give users insight into their holdings ([GitHub - PlebRick/BTCTX: Bitcoin portfolio and capital gains tracker](https://github.com/PlebRick/BTCTX#:~:text=%2A%20Year,2FA%2C%20or%20advanced%20analytics%20dashboards)).
* **Broad Deployability** – Make BitcoinTX easy to deploy in various environments. This includes providing Docker images/Compose setups for one-command deployment and possibly packaging the app for self-hosting solutions like Start9’s StartOS (Embassy) ([GitHub - PlebRick/BTCTX: Bitcoin portfolio and capital gains tracker](https://github.com/PlebRick/BTCTX#:~:text=,hosting%20solutions%20like%20Start9%27s%20StartOS)). The goal is to enable non-developers to run their own instance with minimal setup.

---

## Miscellaneous

* **Branching Strategy** – Code is merged into `master` only after being tested in feature branches or a `dev` branch. This ensures the `master` branch is relatively stable at any given time.
* **Versioning** – The project will follow semantic versioning once an initial stable release is ready (currently in pre-release development).
* **Security** – Although BitcoinTX is intended for single-user use, security best practices are followed. This includes proper password hashing (using bcrypt), using HTTPS in production, and minimizing exposed services. User keys or sensitive data are not stored on the server except as necessary, and future enhancements like 2FA will further harden access.
