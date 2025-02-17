import React, { useEffect, useState } from "react";
import axios from "axios";
import TransactionPanel from "../components/TransactionPanel";
import "../styles/transactions.css";

/**
 * -----------------------------------------------------------
 * 1) ITransaction interface (Double-Entry)
 * -----------------------------------------------------------
 * The backend now returns `from_account_id` and `to_account_id`, 
 * instead of a single 'account_id'. We reflect that below.
 */
interface ITransaction {
  id: number;
  from_account_id: number;
  to_account_id: number;
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
 * accountIdToName: 
 * Convert numeric IDs to a string label.
 *   1 => Bank
 *   2 => Wallet
 *   3 => Exchange
 *   4 => External
 * Adjust if your backend uses different IDs.
 */
function accountIdToName(id: number): string {
  switch (id) {
    case 1: return "Bank";
    case 2: return "Wallet";
    case 3: return "Exchange";
    case 4: return "External";
    default: return `Acct #${id}`;
  }
}

/**
 * resolveDisplayAccount: 
 * For the "Account" column, we need to choose which side to show
 * (from_account or to_account) based on the transaction type.
 */
function resolveDisplayAccount(tx: ITransaction): string {
  const { type, from_account_id, to_account_id } = tx;
  switch (type) {
    case "Deposit":
      // user deposit => from=External(4) => to=userAccts
      return accountIdToName(to_account_id);
    case "Withdrawal":
      // user withdrawal => from=userAccts => to=External(4)
      return accountIdToName(from_account_id);
  
      // a transfer => from -> to
      case "Transfer": {
        const fromLabel = accountIdToName(from_account_id);
        const toLabel = accountIdToName(to_account_id);
        return `${fromLabel} -> ${toLabel}`;
      }
      
    case "Buy":
    case "Sell":
      // typically from=3, to=3 => "Exchange"
      return "Exchange";
    default:
      return "???";
  }
}

/**
 * formatAmount: 
 * Show a single textual representation of amounts. 
 * We rely on transaction type:
 *  - For deposit/withdrawal/transfer: show the USD or BTC that moved. 
 *  - Buy => show "$X -> BTC Y"
 *  - Sell => "BTC Y -> $X"
 */
function formatAmount(tx: ITransaction): string {
  const { type, amount_usd, amount_btc } = tx;

  if (type === "Deposit" || type === "Withdrawal" || type === "Transfer") {
    // One side is typically external or another account. 
    // Show whichever is non-zero. If amount_btc != 0 => BTC, else USD
    if (amount_btc !== 0) {
      return `BTC ${Math.abs(amount_btc)}`;
    }
    return `$${Math.abs(amount_usd)}`;
  }

  if (type === "Buy") {
    return `$${amount_usd} -> BTC ${amount_btc}`;
  }
  if (type === "Sell") {
    return `BTC ${amount_btc} -> $${amount_usd}`;
  }

  return "";
}

/**
 * formatExtra:
 * - Deposit => show 'source' if not "N/A"
 * - Withdrawal => show 'purpose' if not "N/A"
 * - Could be extended for Buy/Sell to show cost basis or something else
 */
function formatExtra(tx: ITransaction): string {
  const { type, source, purpose } = tx;
  if (type === "Deposit" && source !== "N/A") {
    return source;
  }
  if (type === "Withdrawal" && purpose !== "N/A") {
    return purpose;
  }
  return "";
}

/**
 * Transactions Page
 * Shows a list of existing transactions, grouped by date, 
 * plus a button to open TransactionPanel for new transactions.
 */
const Transactions: React.FC = () => {
  // (1) Panel open/close
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  // (2) Transactions + sort mode
  const [transactions, setTransactions] = useState<ITransaction[]>([]);
  const [sortMode, setSortMode] = useState<SortMode>("TIMESTAMP_DESC");

  // (3) Loading / error
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * fetchTransactions:
   * Load the double-entry transactions from the backend,
   * which now have from_account_id / to_account_id in the response.
   */
  async function fetchTransactions() {
    setLoading(true);
    setError(null);
    try {
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

  // After new transaction submitted => refresh
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
   * Group by date
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
      {/* Add Transaction button => opens the panel */}
      <button className="accent-btn" onClick={openPanel}>
        Add Transaction
      </button>

      {/* Sort dropdown */}
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

      {/* Loading & Error */}
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
                const timeStr = new Date(tx.timestamp).toLocaleTimeString(
                  "en-US",
                  { hour: "numeric", minute: "2-digit" }
                );
                const accountLabel = resolveDisplayAccount(tx);
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
                      gap: "1rem",
                      padding: "0.5rem 1rem",
                      marginBottom: "0.5rem",
                      borderRadius: "4px",
                      backgroundColor: "#1b1b1b",
                      color: "#fff",
                    }}
                  >
                    {/* 
                      We'll keep the same columns:
                      1) Time
                      2) Type
                      3) Account (now determined by from/to logic)
                      4) Amount
                      5) Fee
                      6) Extra
                      7) [Edit button placeholder]
                    */}
                    <span style={{ minWidth: "70px" }}>{timeStr}</span>
                    <span style={{ minWidth: "80px" }}>{tx.type}</span>
                    <span style={{ minWidth: "80px" }}>{accountLabel}</span>
                    <span style={{ minWidth: "100px" }}>{amountLabel}</span>
                    <span style={{ minWidth: "80px" }}>{feeLabel}</span>
                    <span style={{ flex: 1 }}>{extraLabel}</span>

                    <button
                      onClick={() => {
                        console.log("Edit transaction", tx.id);
                        // For future: open panel in edit mode
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

      {/* The sliding TransactionPanel for adding new TXs */}
      <TransactionPanel
        isOpen={isPanelOpen}
        onClose={closePanel}
        onSubmitSuccess={handleSubmitSuccess}
      />
    </div>
  );
};

export default Transactions;
