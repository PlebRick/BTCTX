/**
 * Transactions.tsx
 *
 * A page that lists all transactions. Even though the backend now stores 
 * multiple ledger lines per transaction, we still display each transaction 
 * as a single row. If you want more detail in the future, you could expand 
 * to show ledger lines or partial-lot usage.
 */

import React, { useEffect, useState } from "react";
import TransactionPanel from "../components/TransactionPanel";
import "../styles/transactions.css";
import api from "../api"; // Centralized API client (keeps the base URL / config)

// ------------------------------
//  1) IMPORTING HELPER UTILS
// ------------------------------
import {
  parseTransaction,      // We'll call this after fetching the raw data
  formatTimestamp,       // For date/time display if we want to
  formatUsd,             // For USD fields
  formatBtc,             // For BTC amounts
  parseDecimal           // For any direct decimal parsing if needed
} from "../utils/format";

/*
  We do a dummy usage for formatTimestamp / parseDecimal 
  to avoid TS/ESLint "unused variable" errors, 
  while still preserving future availability and comments.
*/
void formatTimestamp;
void parseDecimal;

/**
 * ITransactionRaw:
 * If your backend returns decimals as strings ("50.00000000"),
 * define a minimal interface for the "raw" data shape. 
 * Then we can parse them into real numbers via parseTransaction().
 *
 * Because your final code uses ITransaction with numeric fields,
 * we'll transform from ITransactionRaw -> ITransaction in fetchTransactions.
 */
interface ITransactionRaw {
  id: number;
  from_account_id: number | null;
  to_account_id: number | null;
  type: "Deposit" | "Withdrawal" | "Transfer" | "Buy" | "Sell";

  // The backend returns these numeric fields as strings, e.g. "50.00000000"
  amount?: string | number;
  fee_amount?: string | number;
  cost_basis_usd?: string | number;
  proceeds_usd?: string | number;
  realized_gain_usd?: string | number; // If the server sends realized gain

  // Timestamps are strings
  timestamp: string;
  is_locked: boolean;

  // Additional optional fields
  holding_period?: string | null;
  external_ref?: string | null;
  source?: string | null;
  purpose?: string | null;
  fee_currency?: string;
  created_at?: string;
  updated_at?: string;
}

/**
 * ITransaction interface:
 * Reflects the final backend's Transaction model after parseTransaction(),
 * so all decimal fields (amount, fee_amount, proceeds_usd, realized_gain_usd)
 * are guaranteed numbers.
 */
interface ITransaction {
  id: number;
  from_account_id: number | null;
  to_account_id: number | null;
  type: "Deposit" | "Withdrawal" | "Transfer" | "Buy" | "Sell";

  amount: number;           // single transaction amount (LEGACY) as a real number
  timestamp: string;        // ISO date
  is_locked: boolean;

  // Advanced fields from new double-entry, now numeric
  fee_amount: number;
  fee_currency?: string;
  cost_basis_usd: number;
  proceeds_usd: number;
  realized_gain_usd: number;
  holding_period?: string;
  external_ref?: string;
  source?: string;
  purpose?: string;

  // If needed
  created_at?: string;
  updated_at?: string;
}

/**
 * For sorting. 
 */
type SortMode = "TIMESTAMP_DESC" | "CREATION_DESC";

/**
 * Convert numeric account IDs to a readable label. 
 * In a bigger system, you'd fetch account info from the server,
 * but here we do a quick mapping.
 */
function accountIdToName(id: number | null): string {
  if (id === null) return "N/A";
  switch (id) {
    case 1:
      return "Bank (USD)";
    case 2:
      return "Wallet (BTC)";
    case 3:
      return "Exchange USD";
    case 4:
      return "Exchange BTC";
    case 99:
      return "External";
    default:
      return `Acct #${id}`;
  }
}

/**
 * For each transaction row, we show a single line. 
 * In a pure multi-line ledger world, you might 
 * display each ledger line or let the user expand it.
 */
function resolveDisplayAccount(tx: ITransaction): string {
  const { type, from_account_id, to_account_id } = tx;
  switch (type) {
    case "Deposit":
      return accountIdToName(to_account_id);
    case "Withdrawal":
      return accountIdToName(from_account_id);
    case "Transfer": {
      const fromLabel = accountIdToName(from_account_id);
      const toLabel = accountIdToName(to_account_id);
      return `${fromLabel} -> ${toLabel}`;
    }
    case "Buy":
    case "Sell":
      // Typically from=ExchangeUSD -> to=ExchangeBTC or vice versa
      // We can show "Exchange" or from->to label
      return "Exchange";
    default:
      return "???";
  }
}

/**
 * Format the single 'amount' we show. 
 * In the new system, multiple ledger lines might exist, 
 * but we keep a simplified approach for the UI.
 */
function formatAmount(tx: ITransaction): string {
  const { type, amount, cost_basis_usd, proceeds_usd } = tx;
  switch (type) {
    case "Deposit":
    case "Withdrawal":
    case "Transfer":
      return `${amount}`;

    case "Buy":
      // amount is the USD spent
      return cost_basis_usd
        ? `${formatUsd(cost_basis_usd)} spent`
        : `${formatUsd(amount)} spent`;

    case "Sell":
      // amount is the BTC sold
      // if proceeds_usd is set, we can display it
      return proceeds_usd
        ? `Sold ${formatBtc(amount)} -> ${formatUsd(proceeds_usd)}`
        : `Sold ${formatBtc(amount)}`;

    default:
      return `${amount}`;
  }
}

/**
 * e.g., show 'source' or 'purpose' or short/long holding period.
 */
function formatExtra(tx: ITransaction): string {
  const { type, source, purpose, holding_period } = tx;
  if (type === "Deposit" && source && source !== "N/A") {
    return source;
  }
  if (type === "Withdrawal" && purpose && purpose !== "N/A") {
    return purpose;
  }
  // Could also display short/long etc.
  if (holding_period) {
    return `(${holding_period})`;
  }
  return "";
}

const Transactions: React.FC = () => {
  // State to manage the TransactionPanel open/close
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  // All transactions (after parsing => numeric decimal fields)
  const [transactions, setTransactions] = useState<ITransaction[]>([]);

  // Sorting
  const [sortMode, setSortMode] = useState<SortMode>("TIMESTAMP_DESC");

  // Loading & error states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * fetchTransactions => GET /transactions 
   * The new backend returns "Transaction" objects that might 
   * have decimal fields as strings, e.g. "50.00000000". We fetch them 
   * as ITransactionRaw, then call parseTransaction(...) to convert 
   * them into real numeric fields for ITransaction.
   */
  async function fetchTransactions() {
    setLoading(true);
    setError(null);
    try {
      // 1) Fetch raw data from /transactions
      //    using the same 'api' from '../api' (keeps baseURL / tokens, etc.)
      const res = await api.get<ITransactionRaw[]>("/transactions/");

      // 2) Convert each ITransactionRaw => final ITransaction
      //    by calling parseTransaction (from utils/format.ts)
      const parsed = res.data.map((raw) => parseTransaction(raw));

      // 3) Now 'parsed' is an array of ITransaction with 
      //    numeric amount, fee_amount, proceeds_usd, realized_gain_usd, etc.
      setTransactions(parsed);
    } catch (err) {
      console.error(err);
      setError("Failed to load transactions.");
    } finally {
      setLoading(false);
    }
  }

  // On mount, fetch the data
  useEffect(() => {
    fetchTransactions();
  }, []);

  // Panel controls
  const openPanel = () => setIsPanelOpen(true);
  const closePanel = () => setIsPanelOpen(false);

  /**
   * After creating a transaction, re-fetch the list
   */
  const handleSubmitSuccess = () => {
    setIsPanelOpen(false);
    fetchTransactions();
  };

  /**
   * Sort transactions by chosen mode
   */
  const sortedTransactions = [...transactions].sort((a, b) => {
    if (sortMode === "TIMESTAMP_DESC") {
      return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
    } else {
      // "CREATION_DESC" => sort by ID descending
      return b.id - a.id;
    }
  });

  /**
   * Group by date (e.g., "MMM DD, YYYY") for display
   * If we wanted to use formatTimestamp, we could do:
   *   const dateLabel = formatTimestamp(tx.timestamp);
   * But we'll keep the existing approach for consistency.
   */
  const groupedByDate: Record<string, ITransaction[]> = {};
  for (const tx of sortedTransactions) {
    const dateLabel = new Date(tx.timestamp).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
    if (!groupedByDate[dateLabel]) {
      groupedByDate[dateLabel] = [];
    }
    groupedByDate[dateLabel].push(tx);
  }
  const dateGroups = Object.entries(groupedByDate);

  return (
    <div className="transactions-page" style={{ padding: "1rem" }}>
      <button className="accent-btn" onClick={openPanel}>
        Add Transaction
      </button>

      <div style={{ marginTop: "1rem" }}>
        <label>Sort by: </label>
        <select
          value={sortMode}
          onChange={(e) => setSortMode(e.target.value as SortMode)}
        >
          <option value="TIMESTAMP_DESC">Most Recent Date</option>
          <option value="CREATION_DESC">Last Added (ID)</option>
        </select>
      </div>

      {loading && <p>Loading transactions...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
      {!loading && !error && dateGroups.length === 0 && (
        <p>No transactions found.</p>
      )}

      {/* Render grouped transactions */}
      {!loading && !error && dateGroups.length > 0 && (
        <div className="transactions-list" style={{ marginTop: "1rem" }}>
          {dateGroups.map(([dayLabel, txArray]) => (
            <div key={dayLabel} className="transactions-day-group">
              <h3>{dayLabel}</h3>
              {txArray.map((tx) => {
                // For time, we do a simple toLocaleTimeString
                const timeStr = new Date(tx.timestamp).toLocaleTimeString("en-US", {
                  hour: "numeric",
                  minute: "2-digit",
                });

                const accountLabel = resolveDisplayAccount(tx);
                const amountLabel = formatAmount(tx);

                // Fee (if any)
                const feeNumber = tx.fee_amount ?? 0;
                const feeLabel =
                  feeNumber !== 0
                    ? `Fee: ${feeNumber} ${tx.fee_currency || "USD"}`
                    : "";

                const extraLabel = formatExtra(tx);

                return (
                  <div
                    key={tx.id}
                    className="transaction-card"
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: "1rem",
                      padding: "0.5rem 1rem",
                      marginBottom: "0.5rem",
                      borderRadius: "4px",
                      backgroundColor: "#1b1b1b",
                      color: "#fff",
                    }}
                  >
                    <span style={{ minWidth: "70px" }}>{timeStr}</span>
                    <span style={{ minWidth: "80px" }}>{tx.type}</span>
                    <span style={{ minWidth: "130px" }}>{accountLabel}</span>
                    <span style={{ minWidth: "100px" }}>{amountLabel}</span>
                    <span style={{ minWidth: "120px" }}>{feeLabel}</span>
                    <span style={{ flex: 1 }}>{extraLabel}</span>

                    <button
                      onClick={() => {
                        console.log("Edit transaction", tx.id);
                        // Future: open panel in edit mode or show details
                        alert("Edit functionality TBD");
                      }}
                      style={{
                        backgroundColor: "#333",
                        color: "#fff",
                        border: "1px solid #666",
                        borderRadius: "4px",
                        padding: "0.3rem 0.6rem",
                        cursor: "pointer",
                      }}
                    >
                      Edit
                    </button>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      )}

      {/* TransactionPanel for adding new transactions */}
      <TransactionPanel
        isOpen={isPanelOpen}
        onClose={closePanel}
        onSubmitSuccess={handleSubmitSuccess}
      />
    </div>
  );
};

export default Transactions;
