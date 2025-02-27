/**
 * Transactions.tsx
 *
 * A page that lists all transactions in the BitcoinTX application. Although the backend now
 * stores multiple ledger lines per transaction, we display each transaction as a single row.
 * This version combines the new refactor approach (centralized API, typed parsing utilities)
 * with the older logic that distinguishes BTC vs. USD amounts for Deposit/Withdrawal/Transfer.
 */

import React, { useEffect, useState } from "react";
import TransactionPanel from "../components/TransactionPanel";
import "../styles/transactions.css";
import api from "../api"; // Centralized API client (maintains base URL and config)

// --------------------------------------------------------------------
// 1) Importing Helper Utilities from format.ts
// --------------------------------------------------------------------
// parseTransaction: converts raw API data (with string decimals) into typed ITransaction
// formatTimestamp, formatUsd, formatBtc, parseDecimal: used to present or parse numeric fields
import {
  parseTransaction,
  formatUsd,
  formatBtc,
  formatTimestamp, // not currently used, but imported if needed
  parseDecimal,    // not currently used, but imported if needed
} from "../utils/format";

// Use these 'dummy' references to keep them from being flagged as unused:
void formatTimestamp;
void parseDecimal;

// --------------------------------------------------------------------
// 2) Type Declarations (raw vs. parsed transaction)
//    - Mirroring your updated approach with parseTransaction
// --------------------------------------------------------------------

/**
 * ITransactionRaw Interface
 * Represents the raw data structure returned by the `/api/transactions` endpoint.
 * Numeric fields may arrive as strings (e.g., "50.00000000") from the backend,
 * requiring parseTransaction(...) to convert them to numbers.
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
 * ITransaction Interface
 * Represents the transaction data after parsing. All numeric fields are guaranteed
 * to be numbers, thanks to parseTransaction(...).
 */
interface ITransaction {
  id: number;
  from_account_id: number | null;
  to_account_id: number | null;
  type: "Deposit" | "Withdrawal" | "Transfer" | "Buy" | "Sell";
  amount: number;
  timestamp: string;
  is_locked: boolean;
  fee_amount: number;
  fee_currency?: string;
  cost_basis_usd: number;
  proceeds_usd: number;
  realized_gain_usd: number;
  holding_period?: string;
  external_ref?: string;
  source?: string;
  purpose?: string;
  created_at?: string;
  updated_at?: string;
}

/**
 * SortMode Type
 * Defines the available sorting options in this page's dropdown.
 */
type SortMode = "TIMESTAMP_DESC" | "CREATION_DESC";

// --------------------------------------------------------------------
// 3) Helper for Converting Account IDs to Names
// --------------------------------------------------------------------
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

// --------------------------------------------------------------------
// 4) Decide how to show the "account label" for each transaction
// --------------------------------------------------------------------
function resolveDisplayAccount(tx: ITransaction): string {
  const { type, from_account_id, to_account_id } = tx;

  switch (type) {
    case "Deposit":
      // If it's a Deposit, typically from_account_id=99 (External) -> to_account_id=(1/2/3/4)
      return accountIdToName(to_account_id);
    case "Withdrawal":
      // If it's a Withdrawal, typically from_account_id=(1/2/3/4) -> to_account_id=99 (External)
      return accountIdToName(from_account_id);
    case "Transfer":
      // Transfer from one internal account to another (e.g., from Bank(1) to Wallet(2))
      return `${accountIdToName(from_account_id)} -> ${accountIdToName(to_account_id)}`;
    case "Buy":
    case "Sell":
      // For trades, we often see from=Exchange USD -> to=Exchange BTC or vice versa
      return "Exchange";
    default:
      return "Unknown";
  }
}

// --------------------------------------------------------------------
// 5) Format the 'amount' displayed, distinguishing BTC vs. USD
//    for Deposit/Withdrawal/Transfer (restoring old logic).
// --------------------------------------------------------------------
function formatAmount(tx: ITransaction): string {
  const { type, amount, cost_basis_usd, proceeds_usd, from_account_id, to_account_id } = tx;

  // This switch statement is the heart of the difference from your new code:
  // We don't always assume BTC for deposits/withdrawals/transfers.
  // Instead, we interpret whether it should be BTC or USD, based on the account(s).
  switch (type) {
    case "Deposit":
      // If deposit, the to_account_id is receiving the funds
      if (to_account_id === 1 || to_account_id === 3) {
        // 1 = Bank (USD), 3 = Exchange USD -> interpret deposit as USD
        return formatUsd(amount);
      } else {
        // Otherwise 2 = Wallet (BTC), 4 = Exchange BTC -> interpret deposit as BTC
        return formatBtc(amount);
      }

    case "Withdrawal":
      // If withdrawal, the from_account_id is paying out
      if (from_account_id === 1 || from_account_id === 3) {
        // from Bank or Exchange USD -> show as USD
        return formatUsd(amount);
      } else {
        // from a BTC-based account -> show as BTC
        return formatBtc(amount);
      }

    case "Transfer":
      // Transfers can be from a USD account to a BTC account, or vice versa.
      // The "amount" might represent BTC or USD. Decide which side we want to show.
      // (There’s no perfect “both sides” without a bigger UI design.)
      // For simplicity, let's assume the 'amount' is in the currency of the *from* account:
      if (from_account_id === 1 || from_account_id === 3) {
        return `${formatUsd(amount)} transferred`;
      } else {
        return `${formatBtc(amount)} transferred`;
      }

    // For Buy and Sell:
    case "Buy":
      // A "Buy" typically means "buying BTC with USD". cost_basis_usd is how much USD was spent.
      return cost_basis_usd
        ? `${formatUsd(cost_basis_usd)} spent`
        : `${formatUsd(amount)} spent`;

    case "Sell":
      // A "Sell" typically means "selling BTC for USD". proceeds_usd is the USD gained.
      // 'amount' usually is the BTC quantity sold.
      return proceeds_usd
        ? `Sold ${formatBtc(amount)} -> ${formatUsd(proceeds_usd)}`
        : `Sold ${formatBtc(amount)}`;

    default:
      // If some unknown type, fallback to just showing the numeric 'amount'
      return `${amount}`;
  }
}

// --------------------------------------------------------------------
// 6) Show additional info like 'source', 'purpose', or 'holding_period'
// --------------------------------------------------------------------
function formatExtra(tx: ITransaction): string {
  const { type, source, purpose, holding_period } = tx;

  if (type === "Deposit" && source && source !== "N/A") {
    return source; // e.g. "From paycheck" or "Coinbase" etc.
  }
  if (type === "Withdrawal" && purpose && purpose !== "N/A") {
    return purpose; // e.g. "Rent payment"
  }
  if (holding_period) {
    return `(${holding_period})`; // e.g., "(short)" or "(long)"
  }
  return "";
}

// --------------------------------------------------------------------
// 7) Transactions Page Component
// --------------------------------------------------------------------
const Transactions: React.FC = () => {
  // State for controlling the "Add Transaction" panel (TransactionPanel)
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  // State for storing the parsed transactions
  const [transactions, setTransactions] = useState<ITransaction[] | null>(null);

  // Sorting mode (Timestamp descending or creation ID descending)
  const [sortMode, setSortMode] = useState<SortMode>("TIMESTAMP_DESC");

  // Loading and error states
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // ------------------------------------------------------------------
  // fetchTransactions - load data from the backend
  //   - Uses the new centralized API instance
  //   - Parses the raw data into ITransaction
  //   - Enhances error handling (inspired by the new approach)
  // ------------------------------------------------------------------
  const fetchTransactions = async () => {
    setIsLoading(true);
    setFetchError(null);

    try {
      // GET /transactions (baseURL likely includes /api, so this resolves to /api/transactions)
      const res = await api.get<ITransactionRaw[]>("/transactions");
      console.log("Raw API response (transactions):", res.data);

      // Convert raw data (with string decimal fields) to typed numeric fields
      const parsedTransactions = res.data.map(raw => parseTransaction(raw));
      console.log("Parsed transactions:", parsedTransactions);

      setTransactions(parsedTransactions);
    } catch (err) {
      // Provide a more descriptive error
      const errorMsg =
        err instanceof Error
          ? `Failed to load transactions: ${err.message}`
          : "Failed to load transactions: Unknown error";

      console.error("Fetch error:", err);
      setFetchError(errorMsg);
      setTransactions(null);
    } finally {
      setIsLoading(false);
    }
  };

  // Load transactions on mount
  useEffect(() => {
    fetchTransactions();
  }, []);

  // Open/close the transaction panel
  const openPanel = () => setIsPanelOpen(true);
  const closePanel = () => setIsPanelOpen(false);

  // When a new transaction is submitted successfully, refresh the list
  const handleSubmitSuccess = () => {
    setIsPanelOpen(false);
    fetchTransactions();
  };

  // ------------------------------------------------------------------
  // Sorting the transactions array by chosen mode
  // ------------------------------------------------------------------
  const sortedTransactions = transactions
    ? [...transactions].sort((a, b) => {
        if (sortMode === "TIMESTAMP_DESC") {
          // Sort by timestamp descending
          return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
        } else {
          // Sort by ID descending
          return b.id - a.id;
        }
      })
    : [];

  // ------------------------------------------------------------------
  // Group by date label for display
  // ------------------------------------------------------------------
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

  // Convert the grouped object to an array of [dayLabel, txArray] pairs
  const dateGroups = Object.entries(groupedByDate);

  return (
    <div className="transactions-page" style={{ padding: "1rem" }}>
      {/* Add Transaction Button */}
      <button className="accent-btn" onClick={openPanel}>
        Add Transaction
      </button>

      {/* Sorting Dropdown */}
      <div style={{ marginTop: "1rem" }}>
        <label>Sort by: </label>
        <select
          value={sortMode}
          onChange={e => setSortMode(e.target.value as SortMode)}
        >
          <option value="TIMESTAMP_DESC">Most Recent Date</option>
          <option value="CREATION_DESC">Last Added (ID)</option>
        </select>
      </div>

      {/* Loading State */}
      {isLoading && <p>Loading transactions...</p>}

      {/* Error State */}
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
      {!isLoading && !fetchError && transactions && transactions.length === 0 && (
        <p>No transactions found.</p>
      )}

      {/* Transaction List - only show if we have transactions */}
      {!isLoading && !fetchError && transactions && transactions.length > 0 && (
        <div className="transactions-list" style={{ marginTop: "1rem" }}>
          {dateGroups.map(([dayLabel, txArray]) => (
            <div key={dayLabel} className="transactions-day-group">
              <h3>{dayLabel}</h3>
              {txArray.map(tx => {
                const timeStr = new Date(tx.timestamp).toLocaleTimeString("en-US", {
                  hour: "numeric",
                  minute: "2-digit",
                });

                // Determine how to label the account(s)
                const accountLabel = resolveDisplayAccount(tx);

                // Format the main transaction amount, using new logic to differentiate BTC vs. USD
                const amountLabel = formatAmount(tx);

                // Format the fee, if present
                const feeLabel = tx.fee_amount
                  ? `Fee: ${formatUsd(tx.fee_amount)} ${tx.fee_currency || "USD"}`
                  : "";

                // Format extra detail like source/purpose/holding_period
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

                    {/* Example "Edit" button (not fully implemented) */}
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
