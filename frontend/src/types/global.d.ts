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
   */
  interface GainsAndLossesRaw {
    sells_proceeds: string | number;
    withdrawals_spent: string | number;
    income_earned: string | number;
    interest_earned: string | number;
    fees: {
      USD: string | number;
      BTC: string | number;
    };
    total_gains: string | number;
    total_losses: string | number;
  }

  /**
   * Parsed GainsAndLosses after numeric conversions. All
   * relevant fields are guaranteed to be `number`.
   */
  interface GainsAndLosses {
    sells_proceeds: number;
    withdrawals_spent: number;
    income_earned: number;
    interest_earned: number;
    fees: {
      USD: number;
      BTC: number;
    };
    total_gains: number;
    total_losses: number;
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
