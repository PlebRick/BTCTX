/**
 * global.d.ts
 *
 * Ambient type declarations for the entire frontend.
 * By placing interfaces and types in the global scope, we avoid
 * duplicating domain models in each file.
 *
 * Make sure this file is included in tsconfig.json so TypeScript picks it up.
 */

declare global {
  // --------------------------------------------------------------
  // 1) Domain Models for Account Balances & Gains/Losses
  // --------------------------------------------------------------

  /**
   * Represents an account balance row returned by the server.
   * The `balance` can be a number or string; we parse it to ensure
   * numeric usage in the UI (via parseDecimal).
   */
  interface AccountBalance {
    account_id: number;
    name: string;
    currency: string;
    balance: number | string;
  }

  /**
   * Raw GainsAndLosses data from the backend, where numeric fields
   * may be string or number. We parse them into real numbers in the UI.
   *
   * Note:
   *  - Some fields may be missing if the server is older, so we mark them optional with `?:`.
   *  - The short/long term fields are also optional.
   */
  interface GainsAndLossesRaw {
    // --------------------- Legacy + existing fields ---------------------
    sells_proceeds?: string | number;
    withdrawals_spent?: string | number;
    income_earned?: string | number;
    interest_earned?: string | number;
    rewards_earned?: string | number;
    gifts_received?: string | number;
    realized_gains?: string | number;
    total_income?: string | number;
    fees?: {
      USD?: string | number;
      BTC?: string | number;
    };
    total_gains?: string | number;
    total_losses?: string | number;

    // --------------------- Old short/long fields (backward compat) ---------------------
    /**
     * Used by older code to track short-term realized gains.
     * Replaced by the more detailed short_term_gains / short_term_losses, but still present for compatibility.
     */
    short_term_realized_gains?: string | number;

    /**
     * Used by older code to track long-term realized gains.
     * Replaced by the more detailed long_term_gains / long_term_losses, but still present for compatibility.
     */
    long_term_realized_gains?: string | number;

    /**
     * Possibly the sum of short+long realized gains. Retained for older code usage.
     */
    total_realized_gains_usd?: string | number;

    // --------------------- NEW detailed short/long fields ---------------------
    /**
     * The total short-term *gains* portion (positive numbers only).
     */
    short_term_gains?: string | number;

    /**
     * The total short-term *losses* portion (positive numbers only).
     */
    short_term_losses?: string | number;

    /**
     * The net short-term result (gains - losses). Can be negative or positive.
     */
    short_term_net?: string | number;

    /**
     * The total long-term *gains* portion (positive numbers only).
     */
    long_term_gains?: string | number;

    /**
     * The total long-term *losses* portion (positive numbers only).
     */
    long_term_losses?: string | number;

    /**
     * The net long-term result (gains - losses). Can be negative or positive.
     */
    long_term_net?: string | number;

    /**
     * The overall net capital gains/losses across short & long.
     */
    total_net_capital_gains?: string | number;

    // --------------------- NEW BTC fields for Income, Interest, Rewards, Gifts ---------------------
    /**
     * The total BTC amount for deposits with source = "Income".
     */
    income_btc?: string | number;

    /**
     * The total BTC amount for deposits with source = "Interest".
     */
    interest_btc?: string | number;

    /**
     * The total BTC amount for deposits with source = "Reward".
     */
    rewards_btc?: string | number;

    /**
     * The total BTC amount for deposits with source = "Gift".
     */
    gifts_btc?: string | number;
  }

  /**
   * Parsed GainsAndLosses after numeric conversions. All
   * relevant fields are guaranteed to be `number` (defaulting to 0 if missing).
   */
  interface GainsAndLosses {
    // --------------------- Legacy + existing fields ---------------------
    sells_proceeds: number;
    withdrawals_spent: number;
    income_earned: number;
    interest_earned: number;
    rewards_earned: number;
    gifts_received: number;
    realized_gains: number;
    total_income: number;
    fees: {
      USD: number;
      BTC: number;
    };
    total_gains: number;
    total_losses: number;

    // --------------------- Old short/long fields (backward compat) ---------------------
    short_term_realized_gains?: number;    // might be 0 or undefined if older backend
    long_term_realized_gains?: number;     // might be 0 or undefined
    total_realized_gains_usd?: number;     // short+long combined

    // --------------------- NEW detailed short/long fields ---------------------
    short_term_gains: number;             // sum of short-term gains
    short_term_losses: number;            // sum of short-term losses
    short_term_net: number;               // short_term_gains - short_term_losses
    long_term_gains: number;              // sum of long-term gains
    long_term_losses: number;             // sum of long-term losses
    long_term_net: number;                // long_term_gains - long_term_losses
    total_net_capital_gains: number;      // overall net across short & long

    // --------------------- NEW BTC fields for Income, Interest, Rewards, Gifts ---------------------
    /**
     * The total BTC amount for deposits with source = "Income".
     */
    income_btc: number;

    /**
     * The total BTC amount for deposits with source = "Interest".
     */
    interest_btc: number;

    /**
     * The total BTC amount for deposits with source = "Reward".
     */
    rewards_btc: number;

    /**
     * The total BTC amount for deposits with source = "Gift".
     */
    gifts_btc: number;
  }

  // --------------------------------------------------------------
  // 1a) Optional: Bitcoin Price API Types
  // --------------------------------------------------------------

  /**
   * For /bitcoin/price => returns { USD: number }
   * We can store it in a generic object if you track multiple currencies,
   * but typically you just have { USD: 12345.67 }.
   */
  interface LiveBtcPriceResponse {
    USD: number;
  }

  /**
   * For /bitcoin/price/history?days=7 => returns an array
   * of { time: number, price: number } in your code.
   */
  interface BtcPriceHistoryPoint {
    time: number;   // e.g. Unix timestamp in seconds
    price: number;  // in USD
  }

  // --------------------------------------------------------------
  // 2) Domain Models for Transactions
  // --------------------------------------------------------------

  /**
   * Raw transaction data as returned by the backend.
   * Numeric fields may be strings (e.g. "0.00010000").
   * Optional fields might be null.
   */
  interface ITransactionRaw {
    id: number;
    from_account_id: number | null;
    to_account_id: number | null;
    type: "Deposit" | "Withdrawal" | "Transfer" | "Buy" | "Sell";
    amount?: string | number;
    fee_amount?: string | number;
    cost_basis_usd?: string | number;
    proceeds_usd?: string | number;
    realized_gain_usd?: string | number;
    timestamp: string;
    is_locked: boolean;
    holding_period?: string | null;
    external_ref?: string | null;
    source?: string | null;
    purpose?: string | null;
    fee_currency?: string;
    created_at?: string;
    updated_at?: string;
  }

  /**
   * Final transaction data in the UI, where numeric fields
   * are guaranteed `number` and null -> undefined for strings.
   */
  interface ITransaction {
    id: number;
    from_account_id: number | null;
    to_account_id: number | null;
    type: "Deposit" | "Withdrawal" | "Transfer" | "Buy" | "Sell";
    amount: number;
    fee_amount: number;
    cost_basis_usd: number;
    proceeds_usd: number;
    realized_gain_usd: number;
    timestamp: string;
    is_locked: boolean;
    holding_period?: string;
    external_ref?: string;
    source?: string;
    purpose?: string;
    fee_currency?: string;
    created_at?: string;
    updated_at?: string;
  }

  /**
   * Sorting options for the Transactions page.
   */
  type SortMode = "TIMESTAMP_DESC" | "CREATION_DESC";

  /**
   * IAccountMapping:
   * The return shape from a function like mapDoubleEntryAccounts(...).
   */
  interface IAccountMapping {
    from_account_id: number;
    to_account_id: number;
  }

  /**
   * ICreateTransactionPayload:
   * The shape of the final payload POSTed to /transactions.
   * The backend interprets it as multiple ledger lines (double-entry).
   */
  interface ICreateTransactionPayload {
    from_account_id: number;
    to_account_id: number;
    type: TransactionType;
    amount: number;
    timestamp: string;         // ISO8601
    fee_amount: number;
    fee_currency: Currency;    // "USD" or "BTC"
    cost_basis_usd: number;
    proceeds_usd?: number;     // optional for certain transactions
    source?: string;
    purpose?: string;
    is_locked: boolean;
  }

  interface ApiErrorResponse {
    detail?: string;
    errors?: Record<string, string[]>; // if your server returns field‐specific errors
  }

  // --------------------------------------------------------------
  // 3) Types for the TransactionForm
  // --------------------------------------------------------------

  /**
   * The possible transaction types the user can select in the UI.
   */
  type TransactionType = "Deposit" | "Withdrawal" | "Transfer" | "Buy" | "Sell";

  /**
   * The account type options shown in the UI (simple textual representation).
   */
  type AccountType = "Bank" | "Wallet" | "Exchange";

  /**
   * For deposit sources, e.g. "Income", "Gift", "N/A".
   *   - "Income" / "Interest" / "Reward" = counts as income in GainsAndLosses.
   *   - "Gift" = track cost basis, but not counted as income.
   */
  type DepositSource = "N/A" | "MyBTC" | "Gift" | "Income" | "Interest" | "Reward";

  /**
   * For withdrawal purposes, e.g. "Spent", "Gift", "Donation", "Lost".
   */
  type WithdrawalPurpose = "N/A" | "Spent" | "Gift" | "Donation" | "Lost";

  /**
   * Supported currency in the UI: "USD" or "BTC".
   */
  type Currency = "USD" | "BTC";

  /**
   * Data structure used by TransactionForm to handle user inputs
   * for single-entry style. The new backend transforms these into
   * double-entry ledger lines behind the scenes.
   */
  interface TransactionFormData {
    type: TransactionType;
    timestamp: string;

    // Single-account transactions
    account?: AccountType;
    currency?: Currency;
    amount?: number;
    source?: DepositSource;      // For BTC deposit
    purpose?: WithdrawalPurpose; // For BTC withdrawal
    fee?: number;
    costBasisUSD?: number;
    proceeds_usd?: number;

    // Transfer
    fromAccount?: AccountType;
    fromCurrency?: Currency;
    toAccount?: AccountType;
    toCurrency?: Currency;
    amountFrom?: number;
    amountTo?: number;

    // Buy/Sell
    amountUSD?: number;
    amountBTC?: number;
  }

  // --------------------------------------------------------------
  // 4) Types for the Calculator
  // --------------------------------------------------------------

  /**
   * Supported operations in the Calculator component.
   */
  type Operation = "+" | "-" | "*" | "/" | null;
}

export {}; // Required to convert this file into a module.
