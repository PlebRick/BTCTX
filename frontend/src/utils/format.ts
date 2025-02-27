/* FILE: src/utils/format.ts */

/**
 * Utility module for formatting and parsing data in the BitcoinTX application.
 * Provides functions to handle decimal parsing, currency formatting, date/time
 * formatting, and transaction/gains parsing for consistent data handling.
 */

/**
 * --------------------------------------------------------------------------
 * 1) Decimal Parsing
 * --------------------------------------------------------------------------
 */

/**
 * Safely parse a string (or number) into a JavaScript number.
 * - Handles backend responses where numeric fields might be strings (e.g., "50.00000000").
 * - Returns the number if already numeric, parses strings with parseFloat, or defaults to 0 if invalid.
 * @param value - The value to parse, can be string, number, or undefined.
 * @returns A number, defaulting to 0 if parsing fails or value is null/undefined.
 */
export function parseDecimal(value?: string | number): number {
  if (value == null) return 0;
  if (typeof value === "number") return value;
  const parsed = parseFloat(value);
  return Number.isNaN(parsed) ? 0 : parsed;
}

/**
 * --------------------------------------------------------------------------
 * 2) Numeric Formatting
 * --------------------------------------------------------------------------
 */

/**
 * Format a number as USD with 2 decimal places.
 * - Used for displaying USD amounts (e.g., cost basis, proceeds) in the UI.
 * @param amount - The number to format.
 * @returns A string with USD format (e.g., "$50.00").
 */
export function formatUsd(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

/**
 * Format a number as BTC with up to 8 decimal places.
 * - Used for displaying Bitcoin amounts in the UI, reflecting BTC’s precision.
 * @param amount - The number to format.
 * @returns A string with BTC format (e.g., "0.12345678 BTC").
 */
export function formatBtc(amount: number): string {
  return `${amount.toFixed(8)} BTC`;
}

/**
 * --------------------------------------------------------------------------
 * 3) Date/Time Formatting
 * --------------------------------------------------------------------------
 */

/**
 * Format an ISO timestamp into a human-readable string.
 * - Used for displaying transaction timestamps in a consistent format.
 * @param isoString - The ISO timestamp string (e.g., "2025-02-26T12:00:00Z").
 * @returns A formatted string (e.g., "Feb 26, 2025, 12:00 PM") or "Invalid Date" if invalid.
 */
export function formatTimestamp(isoString: string): string {
  if (!isoString) return "Invalid Date";
  const d = new Date(isoString);
  if (isNaN(d.getTime())) return "Invalid Date";
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

/**
 * --------------------------------------------------------------------------
 * 4) Parsing Helpers for Transaction / GainsAndLosses
 * --------------------------------------------------------------------------
 *
 * These helpers transform raw backend data into type-safe, UI-ready formats.
 * - Interfaces define raw and parsed data shapes.
 * - Parsing functions ensure numeric fields are numbers and optional fields are normalized.
 */

/**
 * Interface for raw transaction data as received from the backend.
 * - Numeric fields (amount, fee_amount, etc.) may be strings or numbers.
 * - Optional fields (holding_period, etc.) may include null from the backend.
 * - Matches the structure in Transactions.tsx’s ITransactionRaw.
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
 * Interface for parsed transaction data used in the UI.
 * - Numeric fields are guaranteed to be numbers.
 * - Optional fields are normalized to string | undefined (no null).
 * - Matches the structure in Transactions.tsx’s ITransaction.
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
 * Parses raw transaction data from the backend into a UI-ready format.
 * - Converts string-based numeric fields (e.g., "50.00000000") to numbers.
 * - Normalizes optional string fields by converting null to undefined.
 * - Fixes the TypeScript error in Transactions.tsx by ensuring the output matches ITransaction.
 * - Replaces the original generic parseTransaction to provide a specific, safe transformation.
 * @param rawTx - The raw transaction data from the backend.
 * @returns A parsed transaction object conforming to ITransaction.
 */
export function parseTransaction(rawTx: ITransactionRaw): ITransaction {
  return {
    // Core fields copied directly, no parsing needed
    id: rawTx.id,
    from_account_id: rawTx.from_account_id,
    to_account_id: rawTx.to_account_id,
    type: rawTx.type,
    timestamp: rawTx.timestamp,
    is_locked: rawTx.is_locked,

    // Numeric fields parsed to ensure they are numbers, defaulting to 0 if undefined
    amount: parseDecimal(rawTx.amount),
    fee_amount: parseDecimal(rawTx.fee_amount),
    cost_basis_usd: parseDecimal(rawTx.cost_basis_usd),
    proceeds_usd: parseDecimal(rawTx.proceeds_usd),
    realized_gain_usd: parseDecimal(rawTx.realized_gain_usd),

    // Optional string fields normalized: null becomes undefined to match ITransaction
    holding_period: rawTx.holding_period ?? undefined,
    external_ref: rawTx.external_ref ?? undefined,
    source: rawTx.source ?? undefined,
    purpose: rawTx.purpose ?? undefined,
    fee_currency: rawTx.fee_currency ?? undefined,
    created_at: rawTx.created_at ?? undefined,
    updated_at: rawTx.updated_at ?? undefined,
  };
}

/**
 * RawGainsAndLosses:
 * Minimally describes fields that might be decimal strings in Gains/Losses data.
 * - Unchanged from original, as it’s not involved in the Transactions.tsx error.
 */
interface RawGainsAndLosses {
  sells_proceeds?: string | number;
  withdrawals_spent?: string | number;
  income_earned?: string | number;
  interest_earned?: string | number;
  total_gains?: string | number;
  total_losses?: string | number;
  fees?: {
    USD?: string | number;
    BTC?: string | number;
  };
}

/**
 * parseGainsAndLosses<T>:
 * - Parses raw Gains/Losses data into a numeric format.
 * - Unchanged from original, as it’s not related to the Transactions.tsx error.
 * @param raw - The raw Gains/Losses data.
 * @returns Parsed data with numeric fields.
 */
export function parseGainsAndLosses<T extends RawGainsAndLosses>(raw: T): T & {
  sells_proceeds: number;
  withdrawals_spent: number;
  income_earned: number;
  interest_earned: number;
  total_gains: number;
  total_losses: number;
  fees: {
    USD: number;
    BTC: number;
  };
} {
  return {
    ...raw,
    sells_proceeds: parseDecimal(raw.sells_proceeds),
    withdrawals_spent: parseDecimal(raw.withdrawals_spent),
    income_earned: parseDecimal(raw.income_earned),
    interest_earned: parseDecimal(raw.interest_earned),
    fees: {
      USD: parseDecimal(raw.fees?.USD),
      BTC: parseDecimal(raw.fees?.BTC),
    },
    total_gains: parseDecimal(raw.total_gains),
    total_losses: parseDecimal(raw.total_losses),
  };
}