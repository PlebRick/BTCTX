/* utils/format.ts */

/**
 * --------------------------------------------------------------------------
 * 1) Decimal Parsing
 * --------------------------------------------------------------------------
 */

/**
 * Safely parse a string (or number) into a JS number.
 * If `value` is already a number, just return it.
 * If it’s a string, do parseFloat.
 * If parsing fails or is NaN, return 0.
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
 * Format a number as USD with 2 decimals.
 * e.g. 50 -> "$50.00"
 *      50.1234 -> "$50.12" (rounded)
 */
export function formatUsd(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

/**
 * Format a number as BTC with up to 8 decimals.
 * e.g. 0.0001 -> "0.00010000 BTC"
 *      1.23456789 -> "1.23456789 BTC"
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
 * Format an ISO8601 timestamp into a more user-friendly string
 * with no seconds, e.g. "Sep 10, 2025, 12:34 PM".
 * If invalid, returns "Invalid Date".
 */
export function formatTimestamp(isoString: string): string {
  if (!isoString) return "Invalid Date";
  const d = new Date(isoString);
  if (isNaN(d.getTime())) return "Invalid Date";

  // Example: "Sep 10, 2025, 12:34 PM"
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
 * We define minimal interfaces so TypeScript knows which fields might be
 * string-based decimals. Then we create parseTransaction/parseGainsAndLosses
 * with generics so they accept any object that "extends" these base interfaces.
 * This way, we avoid `any` and keep the code flexible and typed.
 */

/**
 * RawTransaction:
 * Minimally describes fields that might be decimal strings on a Transaction.
 * If your actual backend has more fields, that's fine—any extra fields will
 * be preserved by using a generic type T.
 */
interface RawTransaction {
  amount?: string | number;
  fee_amount?: string | number;
  cost_basis_usd?: string | number;
  proceeds_usd?: string | number;
  // ... add more if needed
}

/**
 * parseTransaction<T>:
 * - T extends RawTransaction => T must at least have the fields above,
 *   but can have more (id, type, timestamp, etc.).
 * - Returns T with those decimal-like fields replaced by real numbers.
 */
export function parseTransaction<T extends RawTransaction>(rawTx: T): T & {
  amount: number;
  fee_amount: number;
  cost_basis_usd: number;
  proceeds_usd: number;
} {
  return {
    ...rawTx,
    amount: parseDecimal(rawTx.amount),
    fee_amount: parseDecimal(rawTx.fee_amount),
    cost_basis_usd: parseDecimal(rawTx.cost_basis_usd),
    proceeds_usd: parseDecimal(rawTx.proceeds_usd),
  };
}

/**
 * RawGainsAndLosses:
 * Minimally describes fields that might be decimal strings in Gains/Losses data.
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
  // ... add more if needed
}

/**
 * parseGainsAndLosses<T>:
 * - T extends RawGainsAndLosses => T must at least have the Gains/Losses fields,
 *   but can contain more (e.g. extra metadata).
 * - Returns T with those decimal fields replaced by real numbers.
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
