# Project To-Do List

This TODO outlines the near-term tasks and longer-term roadmap for BitcoinTX. Items are organized by priority/timeframe, with checkboxes for tracking progress. Additional details are provided to guide implementation.

## Short-Term Tasks (Next Steps)

* [ ] **Finalize Double-Entry System Refactor (Hybrid Ledger)**
  * Adjust the database schema to fully support double-entry accounting. For now, transfers create two transaction records (debit and credit); extend this to other transaction types or consider a new `JournalEntry` model to link debits/credits.
  * Update backend logic so that every transaction operation creates  **balanced entries** : e.g., a *buy* should debit a cash account and credit the BTC account, a *sell* vice versa. This may involve introducing an idea of an external or fiat account for the opposite side of trades.
  * Ensure that creating or editing a transaction either **writes both entries or none** (maintain atomicity). Implement any necessary linking (such as a `transfer_id` field or foreign key) between the two entries of a transaction event.
  * **Status** : *In progress.* Internal transfers now generate two entries as intended ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=1,success%20messages%20to%20the%20frontend)). Next steps are to implement this for deposits/withdrawals (perhaps treating an external wallet as a counter-account) and for buys/sells (linking to a fiat account or an “external” account to balance the trade).
* [ ] **Cost Basis Calculation Improvements (FIFO logic)**
  * Implement a First-In-First-Out algorithm for tracking cost basis across multiple purchases. When a portion of BTC is sold or transferred out, the system should determine which earlier deposits to draw from.
  * Maintain a record of "lots" (amounts of BTC with their acquisition cost and date). Deduct from these lots when processing a sale/withdrawal to calculate realized profit or loss.
  * Update transaction records to store realized gains for each sale (or prepare the data for reporting). For example, if 0.5 BTC is sold, the system might allocate 0.3 BTC from one lot and 0.2 BTC from another, computing the weighted gain.
  * **Implementation detail** : Consider adding a table or extending the Transaction model to keep track of remaining lot quantities and their cost_basis_usd. This will help in generating accurate tax reports.
  * **Reference** : Robust FIFO cost basis handling is a planned feature ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=%2A%20Full%20Double,term%20gains%2C%20Form%208949%20exports)) and is essential for correct tax calculations.
* [ ] **Year-End Lock Mechanism**
  * Define how to  **lock transactions by date** . A simple approach is to have a cutoff date (e.g., December 31 of the last closed year) and mark all transactions up to that date as locked. This could use a global setting or a flag on each transaction (the existing `is_locked` flag) to indicate no edits are allowed ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=,prepared%20for%20locking%20old%20transactions)).
  * Implement backend enforcement: any attempt to edit or delete a locked transaction should be rejected with an appropriate error. Similarly, the frontend should disable editing UI for locked entries (perhaps visually indicated with a lock icon or greyed-out state).
  * Provide a way for the user to **lock a year** (for instance, a button or an automatic process when the new year starts). Once locked, also consider exporting or snapshotting the data for that year (to support the archiving goal later).
  * Test the locking mechanism thoroughly to ensure that once a year is closed, the financial data for that period remains consistent and unaltered.
* [ ] **Frontend: Update Transaction Form for Double-Entry**
  * Modify the transaction form UI to support selecting two accounts for a transfer (one as the source, one as the destination) ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=%2A%20React%20App%20%3A%20Single,entry%20to%20ensure%20accurate%20logging)). Ensure that when "Transfer" type is selected, two account dropdowns are shown.
  * For transaction types like  *Buy/Sell* , consider allowing the user to specify the counterparty account (e.g., a fiat account for a buy, or a fiat destination for a sell). If full double-entry for these types is not yet ready, at minimum prepare the UI to capture the information (perhaps an "External" account option).
  * Add front-end validation to prevent common errors, such as selecting the same account as both source and destination in a transfer, or entering a transfer amount that exceeds the source account’s balance (if such validation is feasible client-side).
  * Ensure the form’s state management (with React Hook Form) accommodates the additional fields. This might involve updating the form schema and default values when the transaction type changes.
  * **Note** : These UI changes go hand-in-hand with backend changes. The form should match the API – for example, if the API expects a `from_account_id` and `to_account_id` for transfers, the form needs to provide those.
* [ ] **Frontend: Build Out Dashboard with Live Data**
  * Integrate a live Bitcoin price feed on the dashboard ([BTCTX/TODO.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/TODO.md#:~:text=Frontend%20Tasks)). Use a reliable public API (e.g., CoinGecko or CoinDesk) to fetch the current BTC-USD price. This will allow the dashboard to show the **current portfolio value** in fiat.
  * Display key summary metrics on the dashboard: for example, total BTC held across all accounts, total value in USD (BTC amount * current price), and perhaps unrealized gains. This provides the user an at-a-glance view of their portfolio status.
  * **Backend support** : Create an endpoint (if not existing) to retrieve aggregate data – e.g., total BTC balance per account and overall. Alternatively, have the frontend compute totals by summing the balances of all accounts it fetched.
  * Show a list of accounts with their balances on the dashboard, and a total. If multiple accounts exist (e.g., different wallets), the dashboard should list each with its BTC balance and equivalent USD value (using live price).
  * Ensure the dashboard data updates periodically. Implement polling or web socket updates for the price, or at least refresh the price each time the dashboard is viewed. (Keep it modest to avoid rate-limit issues with the external API.)
* [ ] **Testing: Increase Coverage & Integration Tests**
  * Write integration tests for the new double-entry behavior. For example, test that creating a transfer via the API results in **two** Transaction records in the database and that their values are correct and opposite. Also test editing a transfer (both entries update appropriately) and deleting a transfer (both entries remove).
  * Add tests for the cost basis calculations. Create scenarios with multiple buys and sells and verify that the computed gains match expected results. This might involve unit-testing the FIFO utility functions with known inputs.
  * Frontend testing: once the transaction form is updated, use React Testing Library to simulate a user filling out a transfer and ensure the form validation works and the correct API call is made. Similarly, test that the dashboard properly displays data given mock API responses for account balances and price.
  * Set up a continuous integration workflow *(if not already present)* to run tests on each push/PR. This will help catch regressions, especially as the project rapidly evolves.

## Long-Term Tasks (Roadmap)

* [ ] **Complete Tax Reporting Features**
  * Implement generation of tax reports such as IRS Form 8949 and Schedule D summaries ([GitHub - PlebRick/BTCTX: Bitcoin portfolio and capital gains tracker](https://github.com/PlebRick/BTCTX#:~:text=Long)). This could be as simple as providing a downloadable CSV of all taxable events (buys/sells with their cost basis and gain/loss) or as advanced as filling PDF forms.
  * Introduce a **tax report view** in the frontend where a user can select a tax year and see a summary of their gains/losses (broken into short-term vs long-term).
  * Ensure that the data in these reports ties back to the transaction ledger (utilizing the FIFO calculations and locked transactions to ensure accuracy).
  * Stay up to date with any relevant tax rules (for example, the user may need to mark transfers between their own wallets as non-taxable events, which the system already does by treating them as internal transfers).
* [ ] **Data Archiving & Performance**
  * As the number of transactions grows (over years of usage), performance could degrade. Plan and implement an **archiving mechanism** for old transactions ([GitHub - PlebRick/BTCTX: Bitcoin portfolio and capital gains tracker](https://github.com/PlebRick/BTCTX#:~:text=,hosting%20solutions%20like%20Start9%27s%20StartOS)). For instance, after a year is locked and tax reports are generated, those transactions could be moved to an archive table or a separate database file.
  * Consider providing a way to export archived years’ data (for backup) and then purge it from the live database to keep it lean. The system should retain opening balances so that even if detailed history is archived, current totals remain correct.
  * Monitor performance on the SQLite database. If needed, provide options to upgrade to a more robust database (PostgreSQL, etc.) for heavy users, or at least optimize queries and use indices for key fields (like date, account, etc.).
  * Test the application with a large number of transactions to identify any bottlenecks, and document guidance (for example, if >10k transactions, consider switching to Postgres).
* [ ] **Multi-User Support**
  * Transition from a single-user system to a multi-user system (if there is demand for it). This would involve creating a user management system: registration, login, and user-specific data segregation (each transaction/account tied to a user).
  * Implement proper authentication and authorization. If using JWT ([BTCTX/README.md at master · PlebRick/BTCTX · GitHub](https://github.com/PlebRick/BTCTX/blob/master/README.md#:~:text=frontend.%20,Web%20Tokens%20for%20session%20management)) or session cookies, ensure each API request is authenticated and only accesses that user’s data.
  * Add administrative controls if necessary (for the initial single user, they might effectively be an “admin” of their instance). For multi-user, consider roles or at least an admin user who can manage others.
  * **Security additions** : Along with multi-user, features like **Two-Factor Authentication (2FA)** become important ([GitHub - PlebRick/BTCTX: Bitcoin portfolio and capital gains tracker](https://github.com/PlebRick/BTCTX#:~:text=%2A%20Year,2FA%2C%20or%20advanced%20analytics%20dashboards)). Plan to integrate an OTP-based 2FA for logins, and possibly email verification for account recovery (though email/SMTP adds complexity to a self-hosted app).
  * Update documentation to guide how to enable multi-user mode (if it’s optional) or how to migrate an existing single-user setup to multi-user.
* [ ] **Enhanced Analytics and Dashboard**
  * Build advanced dashboards for a better overview of the portfolio. This could include charts and graphs (e.g., a line chart of portfolio value over time, pie chart of holdings by account).
  * Provide insights such as **unrealized gains** (based on current price vs cost basis) and even projections or trend analysis. For example, show how much profit/loss is on each lot of BTC held if the user were to sell at current prices.
  * Add a feature to import price history to draw historical value charts. This could use an API to fetch historical BTC prices and then combine with the user’s transactions to show a performance graph.
  * Consider adding alerts or notifications for certain events (e.g., if BTC price crosses a threshold or if a large gain/loss was realized in a day). This is less crucial but could enhance user engagement.
* [ ] **Deployment & Containerization**
  * Create an official Docker image or Docker Compose configuration for BitcoinTX to simplify deployment. This would bundle the FastAPI backend and React frontend, possibly using Nginx or Caddy as a reverse proxy in one container setup.
  * Document the deployment steps for self-hosting (both with Docker and without). Include information on environment variables (refer to `.env.example` for needed settings like `VITE_API_BASE_URL` etc.) and any setup steps (like initializing the database, creating the first user, etc.).
  * Investigate packaging for platforms like **Start9 Labs StartOS (Embassy)** ([GitHub - PlebRick/BTCTX: Bitcoin portfolio and capital gains tracker](https://github.com/PlebRick/BTCTX#:~:text=,hosting%20solutions%20like%20Start9%27s%20StartOS)) or similar self-hosted app ecosystems. This might involve writing a manifest or wrapper according to those platforms’ requirements, enabling users to deploy BitcoinTX as a one-click service on their personal servers.
  * Ensure that security best practices are followed in deployment: for example, instructions for running behind HTTPS, using a strong admin password, and keeping the environment file secrets secure.
* [ ] **Additional Enhancements**
  * **API Improvements** : As the project grows, consider versioning the API and improving error handling/messages for easier client integration.
  * **Mobile-Friendly UI** : Ensure the React frontend is responsive so that the tracker can be used on mobile devices or tablets comfortably. This might involve some layout adjustments in the future.
  * **Plugin/System Export** : Allow users to export all their data (transactions, accounts, etc.) in a common format (JSON or CSV) at any time for backup or if they want to migrate to another system. Similarly, provide an import function to onboard data from other trackers if feasible.
  * **Community and Contributing** : As an open-source project, eventually provide guidelines for others to contribute (coding style, how to run the dev environment, etc.) and possibly a roadmap on GitHub Projects or Issues to coordinate community contributions.

---

*This TODO and Roadmap will be updated as tasks are completed and new goals are set. Contributors are welcome to pick up any open tasks. Be sure to check the `README.md` for overall context and the latest project state before starting on a task.*
