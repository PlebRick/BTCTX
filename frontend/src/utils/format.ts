/* FILE: src/utils/format.ts */

/**
 * Utility module for formatting and parsing data in the BitcoinTX application.
 * Provides functions to handle:
 *  - decimal parsing,
 *  - numeric/currency formatting,
 *  - date/time formatting,
 *  - transaction/gains parsing (based on global domain types).
 */

/**
 * --------------------------------------------------------------------------
 * 1) Decimal Parsing
 * --------------------------------------------------------------------------
 */

/**
 * Safely parse a string (or number) into a JavaScript number.
 *  - Handles backend responses where numeric fields might be strings
 *    (e.g. "50.00000000").
 *  - Returns the number if already numeric, otherwise parseFloat.
 *  - Defaults to 0 if invalid, null, or undefined.
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
 *  - e.g. 50 => "$50.00"
 */
export function formatUsd(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

/**
 * Format a number as BTC with up to 8 decimal places.
 *  - e.g. 0.12345678 => "0.12345678 BTC"
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
 *  - e.g. "2025-02-26T12:00:00Z" => "Feb 26, 2025, 12:00 PM"
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
 * These helpers transform raw backend data (ITransactionRaw, GainsAndLossesRaw)
 * into type-safe, UI-ready formats (ITransaction, GainsAndLosses).
 *
 * No local interface definitions needed — we import them from global.d.ts.
 */

// 1) Import the domain interfaces from global.d.ts
//    - If you have "skipLibCheck": false or "allowJs": etc., this should work
//      automatically. Otherwise, you may do a direct import from a types folder.


/**
 * parseTransaction:
 *  - Converts string-based numeric fields (e.g. "50.00000000") to numbers
 *  - Normalizes null => undefined for optional strings
 *  - Returns an object conforming to ITransaction
 */
export function parseTransaction(rawTx: ITransactionRaw): ITransaction {
  return {
    id: rawTx.id,
    from_account_id: rawTx.from_account_id,
    to_account_id: rawTx.to_account_id,
    type: rawTx.type,
    timestamp: rawTx.timestamp,
    is_locked: rawTx.is_locked,

    // Numeric fields
    amount: parseDecimal(rawTx.amount),
    fee_amount: parseDecimal(rawTx.fee_amount),
    cost_basis_usd: parseDecimal(rawTx.cost_basis_usd),
    proceeds_usd: parseDecimal(rawTx.proceeds_usd),
    realized_gain_usd: parseDecimal(rawTx.realized_gain_usd),

    // Optional fields normalized
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
 * parseGainsAndLosses:
 *  - Parses raw GainsAndLosses data into numeric format.
 *  - Ensures all fields are real numbers, defaulting to 0 if missing.
 */
export function parseGainsAndLosses(raw: GainsAndLossesRaw): GainsAndLosses {
  return {
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
