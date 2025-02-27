/**
 * Transactions.tsx
 *
 * A page that lists all transactions in the BitcoinTX application. Although the backend now stores
 * multiple ledger lines per transaction, we display each transaction as a single row for simplicity.
 * Future enhancements could expand this to show ledger lines or partial-lot usage details.
 */

import React, { useEffect, useState } from "react";
import TransactionPanel from "../components/TransactionPanel";
import "../styles/transactions.css";
import api from "../api"; // Centralized API client (maintains base URL and config)

// ------------------------------
// 1) Importing Helper Utilities
// ------------------------------
import {
  parseTransaction, // Converts raw API data to the desired format
  formatTimestamp,  // Formats timestamps for display (unused but preserved)
  formatUsd,        // Formats USD amounts (e.g., "50.00 USD")
  formatBtc,        // Formats BTC amounts (e.g., "0.50000000 BTC")
  parseDecimal      // Parses string decimals to numbers (unused but preserved)
} from "../utils/format";

// Dummy usage to avoid TS/ESLint "unused variable" warnings while keeping utilities available
void formatTimestamp;
void parseDecimal;

/**
 * ITransactionRaw Interface
 * Represents the raw data structure returned by the `/api/transactions` endpoint.
 * Numeric fields like `amount` may arrive as strings (e.g., "50.00000000") from the backend,
 * requiring parsing via `parseTransaction` into `ITransaction`.
 */
interface ITransactionRaw {
  id: number;
  from_account_id: number | null;
  to_account_id: number | null;
  type: "Deposit" | "Withdrawal" | "Transfer" | "Buy" | "Sell";
  amount?: string | number;           // Transaction amount (string or number)
  fee_amount?: string | number;       // Fee amount (string or number)
  cost_basis_usd?: string | number;   // Cost basis in USD (string or number)
  proceeds_usd?: string | number;     // Proceeds in USD (string or number)
  realized_gain_usd?: string | number;// Realized gain/loss in USD (string or number)
  timestamp: string;                  // ISO timestamp (e.g., "2023-10-01T12:00:00Z")
  is_locked: boolean;                 // Lock status
  holding_period?: string | null;     // Optional holding period (e.g., "short")
  external_ref?: string | null;       // External reference ID
  source?: string | null;             // Source of deposit
  purpose?: string | null;            // Purpose of withdrawal
  fee_currency?: string;              // Currency of the fee (e.g., "USD", "BTC")
  created_at?: string;                // Creation timestamp
  updated_at?: string;                // Last update timestamp
}

/**
 * ITransaction Interface
 * Represents the parsed transaction data after processing with `parseTransaction`.
 * Ensures all numeric fields are numbers for consistent use in the UI.
 */
interface ITransaction {
  id: number;
  from_account_id: number | null;
  to_account_id: number | null;
  type: "Deposit" | "Withdrawal" | "Transfer" | "Buy" | "Sell";
  amount: number;           // Parsed transaction amount
  timestamp: string;        // ISO timestamp (unchanged)
  is_locked: boolean;       // Lock status (unchanged)
  fee_amount: number;       // Parsed fee amount
  fee_currency?: string;    // Fee currency (unchanged)
  cost_basis_usd: number;   // Parsed cost basis in USD
  proceeds_usd: number;     // Parsed proceeds in USD
  realized_gain_usd: number;// Parsed realized gain/loss in USD
  holding_period?: string;  // Optional holding period
  external_ref?: string;    // External reference ID
  source?: string;          // Source of deposit
  purpose?: string;         // Purpose of withdrawal
  created_at?: string;      // Creation timestamp
  updated_at?: string;      // Last update timestamp
}

/**
 * SortMode Type
 * Defines available sorting options for transactions.
 */
type SortMode = "TIMESTAMP_DESC" | "CREATION_DESC";

/**
 * accountIdToName Function
 * Converts numeric account IDs to human-readable labels. In a larger system, this could
 * fetch account details from the server, but here we use a static mapping for simplicity.
 */
function accountIdToName(id: number | null): string {
  if (id === null) return "N/A";
  switch (id) {
    case 1: return "Bank (USD)";
    case 2: return "Wallet (BTC)";
    case 3: return "Exchange USD";
    case 4: return "Exchange BTC";
    case 99: return "External";
    default: return `Acct #${id}`;
  }
}

/**
 * resolveDisplayAccount Function
 * Determines the account label to display based on transaction type, showing a single
 * account or a "from -> to" format for transfers.
 */
function resolveDisplayAccount(tx: ITransaction): string {
  const { type, from_account_id, to_account_id } = tx;
  switch (type) {
    case "Deposit":
      return accountIdToName(to_account_id);
    case "Withdrawal":
      return accountIdToName(from_account_id);
    case "Transfer":
      return `${accountIdToName(from_account_id)} -> ${accountIdToName(to_account_id)}`;
    case "Buy":
    case "Sell":
      return "Exchange"; // Simplified for trades; could expand to from->to
    default:
      return "Unknown";
  }
}

/**
 * formatAmount Function
 * Formats the transaction amount for display, using `formatUsd` and `formatBtc` from `format.ts`
 * to ensure consistent formatting across the application.
 */
function formatAmount(tx: ITransaction): string {
  const { type, amount, cost_basis_usd, proceeds_usd } = tx;
  switch (type) {
    case "Deposit":
    case "Withdrawal":
    case "Transfer":
      return `${formatBtc(amount)}`; // Assumes BTC for simplicity; adjust if USD
    case "Buy":
      return cost_basis_usd
        ? `${formatUsd(cost_basis_usd)} spent`
        : `${formatUsd(amount)} spent`;
    case "Sell":
      return proceeds_usd
        ? `Sold ${formatBtc(amount)} -> ${formatUsd(proceeds_usd)}`
        : `Sold ${formatBtc(amount)}`;
    default:
      return `${amount}`;
  }
}

/**
 * formatExtra Function
 * Provides additional context (e.g., source, purpose, holding period) for display.
 */
function formatExtra(tx: ITransaction): string {
  const { type, source, purpose, holding_period } = tx;
  if (type === "Deposit" && source && source !== "N/A") return source;
  if (type === "Withdrawal" && purpose && purpose !== "N/A") return purpose;
  if (holding_period) return `(${holding_period})`;
  return "";
}

/**
 * Transactions Component
 * Main component for the Transactions page, managing state and rendering the UI.
 */
const Transactions: React.FC = () => {
  // State for TransactionPanel visibility
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  // State for transaction data (parsed into ITransaction)
  const [transactions, setTransactions] = useState<ITransaction[] | null>(null);

  // State for sorting mode
  const [sortMode, setSortMode] = useState<SortMode>("TIMESTAMP_DESC");

  // State for loading and error handling (inspired by Dashboard.tsx)
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  /**
   * fetchTransactions Function
   * Fetches transaction data from the API, parses it, and updates state.
   * Incorporates robust error handling and logging from Dashboard.tsx.
   */
  const fetchTransactions = async () => {
    setIsLoading(true); // Show loading state before fetching
    setFetchError(null); // Clear previous errors
    try {
      // Use the centralized API client to fetch raw transactions
      const res = await api.get<ITransactionRaw[]>("/transactions");
      console.log("Raw API response:", res.data); // Debug raw data

      // Parse raw data into ITransaction format using format.ts utility
      const parsedTransactions = res.data.map((raw) => parseTransaction(raw));
      console.log("Parsed transactions:", parsedTransactions); // Debug parsed data

      setTransactions(parsedTransactions);
    } catch (err: unknown) {
      // Enhanced error handling with detailed messaging
      const errorMessage = err instanceof Error
        ? `Failed to load transactions: ${err.message}`
        : "Failed to load transactions: Unknown error";
      console.error("Fetch error:", err); // Log for debugging
      setFetchError(errorMessage);
      setTransactions(null); // Clear transactions on error
    } finally {
      setIsLoading(false); // Always reset loading state
    }
  };

  // Fetch data on component mount
  useEffect(() => {
    fetchTransactions();
  }, []);

  // TransactionPanel control functions
  const openPanel = () => setIsPanelOpen(true);
  const closePanel = () => setIsPanelOpen(false);

  /**
   * handleSubmitSuccess Function
   * Refreshes the transaction list after a successful submission via TransactionPanel.
   */
  const handleSubmitSuccess = () => {
    setIsPanelOpen(false);
    fetchTransactions();
  };

  // Sort transactions based on selected mode
  const sortedTransactions = transactions
    ? [...transactions].sort((a, b) => {
        if (sortMode === "TIMESTAMP_DESC") {
          return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
        }
        return b.id - a.id; // CREATION_DESC sorts by ID descending
      })
    : [];

  // Group transactions by date for display
  const groupedByDate: Record<string, ITransaction[]> = {};
  for (const tx of sortedTransactions) {
    const dateLabel = new Date(tx.timestamp).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
    if (!groupedByDate[dateLabel]) groupedByDate[dateLabel] = [];
    groupedByDate[dateLabel].push(tx);
  }
  const dateGroups = Object.entries(groupedByDate);

  return (
    <div className="transactions-page" style={{ padding: "1rem" }}>
      {/* Add Transaction Button */}
      <button className="accent-btn" onClick={openPanel}>
        Add Transaction
      </button>

      {/* Sort Dropdown */}
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

      {/* Loading State */}
      {isLoading && <p>Loading transactions...</p>}

      {/* Error State with Retry Option */}
      {fetchError && (
        <div style={{ color: "red", marginTop: "1rem" }}>
          <p>{fetchError}</p>
          <button
            onClick={fetchTransactions}
            style={{
              backgroundColor: "#666",
              color: "#fff",
              border: "none",
              padding: "0.3rem 0.6rem",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            Retry
          </button>
        </div>
      )}

      {/* No Transactions Found */}
      {!isLoading && !fetchError && (!transactions || transactions.length === 0) && (
        <p>No transactions found.</p>
      )}

      {/* Transaction List */}
      {!isLoading && !fetchError && transactions && transactions.length > 0 && (
        <div className="transactions-list" style={{ marginTop: "1rem" }}>
          {dateGroups.map(([dayLabel, txArray]) => (
            <div key={dayLabel} className="transactions-day-group">
              <h3>{dayLabel}</h3>
              {txArray.map((tx) => {
                const timeStr = new Date(tx.timestamp).toLocaleTimeString("en-US", {
                  hour: "numeric",
                  minute: "2-digit",
                });
                const accountLabel = resolveDisplayAccount(tx);
                const amountLabel = formatAmount(tx);
                const feeLabel = tx.fee_amount
                  ? `Fee: ${formatUsd(tx.fee_amount)} ${tx.fee_currency || "USD"}`
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

      {/* TransactionPanel for Adding Transactions */}
      <TransactionPanel
        isOpen={isPanelOpen}
        onClose={closePanel}
        onSubmitSuccess={handleSubmitSuccess}
      />
    </div>
  );
};

export default Transactions;