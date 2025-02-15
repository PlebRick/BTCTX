import React, { useEffect, useState } from "react";
import axios from "axios";
import TransactionPanel from "../components/TransactionPanel";
import "../styles/transactions.css";

/**
 * ITransaction: shape of each record from the backend.
 */
interface ITransaction {
  id: number;
  account_id: number;
  type: "Deposit" | "Withdrawal" | "Transfer" | "Buy" | "Sell";
  amount_usd: number;
  amount_btc: number;
  timestamp: string;   // e.g. ISO date string
  source: string;      // e.g. "Income", "N/A"
  purpose: string;     // e.g. "Gift", "N/A"
  fee: number;
  cost_basis_usd: number;
  is_locked: boolean;
}

/**
 * SortMode: toggles between sorting by newest timestamp 
 * or highest transaction ID.
 */
type SortMode = "TIMESTAMP_DESC" | "CREATION_DESC";

/**
 * A small helper to convert numeric account_id into a string label
 * for display in the "Account" column. Adjust if you have more IDs.
 */
function accountIdToName(id: number): string {
  switch (id) {
    case 1: return "Bank";
    case 2: return "Wallet";
    case 3: return "Exchange";
    default: return `Acct #${id}`; 
}
}

/**
 * A helper to build the single "Amount" column, 
 * depending on transaction type + amounts. 
 * This ensures we do everything in one line for 
 * the "Amount" cell.
 */
function formatAmount(tx: ITransaction): string {
  const { type, amount_usd, amount_btc } = tx;

  // For deposit/withdrawal/transfer, we typically show either
  // "$X" or "BTC X" depending on which is non-zero.
  if (type === "Deposit" || type === "Withdrawal" || type === "Transfer") {
    if (amount_btc !== 0) {
      // e.g. "BTC 0.005"
      return `BTC ${Math.abs(amount_btc)}`;
    } else {
      // e.g. "$500"
      return `$${Math.abs(amount_usd)}`;
    }
  }

  // For Buy => "$X -> BTC Y"
  if (type === "Buy") {
    return `$${amount_usd} -> BTC ${amount_btc}`;
  }

  // For Sell => "BTC Y -> $X"
  if (type === "Sell") {
    return `BTC ${amount_btc} -> $${amount_usd}`;
  }

  // Fallback
  return "";
}

/**
 * Some transactions have an "extra" piece of info:
 * - Deposit => source if not N/A
 * - Withdrawal => purpose if not N/A
 * - Sell => potential future gains
 * etc.
 */
function formatExtra(tx: ITransaction): string {
  const { type, source, purpose } = tx;

  // For deposit, show source if not "N/A"
  if (type === "Deposit" && source !== "N/A") {
    return source;
  }

  // For withdrawal, show purpose if not "N/A"
  if (type === "Withdrawal" && purpose !== "N/A") {
    return purpose;
  }

  // For buy/sell, you might eventually show gain/loss or other placeholders
  // if you track them. For now, we do nothing special for "Buy" or "Sell".

  return ""; // no extra info to display
}

/**
 * Transactions Component
 * ----------------------
 * Fetches + displays transactions grouped by date. 
 * Presents each transaction in a single horizontal row
 * with columns for Time, Type, Account, Amount, Fee, and Extra. 
 */
const Transactions: React.FC = () => {
  // Panel open/close
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  // Transaction data + sort mode
  const [transactions, setTransactions] = useState<ITransaction[]>([]);
  const [sortMode, setSortMode] = useState<SortMode>("TIMESTAMP_DESC");

  // Loading + Error states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * fetchTransactions(): 
   * Loads the transaction list from the backend. 
   */
  async function fetchTransactions() {
    setLoading(true);
    setError(null);
    try {
      // The trailing slash is important to avoid a redirect:
      const res = await axios.get<ITransaction[]>(
        "http://127.0.0.1:8000/api/transactions/"
      );
      setTransactions(res.data);
    } catch (err) {
      console.error(err);
      setError("Failed to load transactions.");
    } finally {
      setLoading(false);
    }
  }

  // Fetch on mount
  useEffect(() => {
    fetchTransactions();
  }, []);

  // Panel controls
  const openPanel = () => setIsPanelOpen(true);
  const closePanel = () => setIsPanelOpen(false);

  // Called after new transaction is submitted => refresh list + close
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
      return b.id - a.id; // "Last Added" => largest id first
    }
  });

  /**
   * Group by date (e.g., "Feb 15, 2025")
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
      {/* 1) "Add Transaction" button */}
      <button className="accent-btn" onClick={openPanel}>
        Add Transaction
      </button>

      {/* 2) Sort dropdown */}
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

      {/* 3) Loading/Error states */}
      {loading && <p>Loading transactions...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
      {!loading && !error && dateGroups.length === 0 && (
        <p>No transactions found.</p>
      )}

      {/* 4) Render the grouped transactions */}
      {!loading && !error && dateGroups.length > 0 && (
        <div className="transactions-list" style={{ marginTop: "1rem" }}>
          {dateGroups.map(([dayLabel, txArray]) => (
            <div 
              key={dayLabel} 
              className="transactions-day-group"
              style={{ marginBottom: "1rem" }}
            >
              <h3>{dayLabel}</h3>
              {txArray.map((tx) => {
                // We'll show only the time (HH:MM) in the row,
                // since the date is already in the heading:
                const timeStr = new Date(tx.timestamp).toLocaleTimeString(
                  "en-US",
                  { hour: "numeric", minute: "2-digit" }
                );

                // Build single-line fields:
                const accountLabel = accountIdToName(tx.account_id);
                const amountLabel = formatAmount(tx);
                const feeLabel = tx.fee !== 0 ? `Fee $${tx.fee}` : "";
                const extraLabel = formatExtra(tx);

                return (
                  <div
                    key={tx.id}
                    className="transaction-card"
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: "1rem", // space between columns
                      padding: "0.5rem 1rem",
                      marginBottom: "0.5rem",
                      borderRadius: "4px",
                      backgroundColor: "#1b1b1b",
                      color: "#fff"
                    }}
                  >
                    {/*
                      Single horizontal row, 6 columns:
                      1) Time
                      2) Type
                      3) Account
                      4) Amount
                      5) Fee
                      6) Extra
                      and a trailing "Edit" button 
                    */}
                    <span style={{ minWidth: "70px" }}>{timeStr}</span>
                    <span style={{ minWidth: "80px" }}>{tx.type}</span>
                    <span style={{ minWidth: "80px" }}>{accountLabel}</span>
                    <span style={{ minWidth: "100px" }}>{amountLabel}</span>
                    <span style={{ minWidth: "80px" }}>{feeLabel}</span>
                    <span style={{ flex: 1 }}>{extraLabel}</span>

                    {/* 
                      Edit button placeholder. 
                      In the future, open the panel in an "edit mode".
                    */}
                    <button
                      onClick={() => {
                        console.log("Edit transaction", tx.id);
                      }}
                      style={{
                        backgroundColor: "#333",
                        color: "#fff",
                        border: "1px solid #666",
                        borderRadius: "4px",
                        padding: "0.3rem 0.6rem",
                        cursor: "pointer"
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

      {/* 5) The TransactionPanel (sliding form) */}
      <TransactionPanel
        isOpen={isPanelOpen}
        onClose={closePanel}
        onSubmitSuccess={handleSubmitSuccess}
      />
    </div>
  );
};

export default Transactions;