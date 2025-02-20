import React, { useEffect, useState } from "react";
import axios from "axios";
import TransactionPanel from "../components/TransactionPanel";
import "../styles/transactions.css";

/**
 * -----------------------------------------------------------
 * 1) ITransaction interface (Double-Entry, new backend schema)
 * -----------------------------------------------------------
 * Matches the refactored backend, which has:
 *  - Single `amount` field
 *  - `fee_amount`, `fee_currency` instead of a single `fee`
 *  - `cost_basis_usd`, `proceeds_usd` for tax calculations
 *  - `source` and `purpose` reintroduced as optional
 *  - We do not have `amount_usd` or `amount_btc` columns anymore.
 */
interface ITransaction {
  id: number;

  from_account_id: number | null;
  to_account_id: number | null;
  type: "Deposit" | "Withdrawal" | "Transfer" | "Buy" | "Sell";

  amount: number;                 // Single transaction amount in the from_account's currency
  timestamp: string;             // e.g. ISO date string
  is_locked: boolean;

  // Optional advanced fields
  fee_amount?: number;
  fee_currency?: string;
  cost_basis_usd?: number;
  proceeds_usd?: number;
  realized_gain_usd?: number;
  holding_period?: string;
  external_ref?: string;

  // Reintroduced deposit/withdrawal metadata
  source?: string;               // e.g. "Income", "Gift", "N/A"
  purpose?: string;              // e.g. "Spent", "Donation", "N/A"

  // (group_id, created_at, updated_at, etc. could also exist if your backend returns them)
}

/**
 * SortMode: toggles between sorting by newest timestamp or highest transaction ID.
 */
type SortMode = "TIMESTAMP_DESC" | "CREATION_DESC";

/**
 * accountIdToName:
 * Convert numeric account IDs to a readable label.
 * We are now using the new IDs: 
 *   1 => Bank
 *   2 => Wallet
 *   3 => ExchangeUSD
 *   4 => ExchangeBTC
 *   99 => External
 * Adjust if your backend uses different IDs.
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
 * resolveDisplayAccount:
 * Decides how to display the "Account" column for each transaction.
 * This logic depends on how you want to label the from/to side for each type.
 */
function resolveDisplayAccount(tx: ITransaction): string {
  const { type, from_account_id, to_account_id } = tx;

  switch (type) {
    case "Deposit":
      // Typically from=External(99), to=user account
      return accountIdToName(to_account_id);

    case "Withdrawal":
      // Typically from=user account, to=External(99)
      return accountIdToName(from_account_id);

    case "Transfer":
      // from -> to
      const fromLabel = accountIdToName(from_account_id);
      const toLabel = accountIdToName(to_account_id);
      return `${fromLabel} -> ${toLabel}`;

    case "Buy":
    case "Sell":
      // Usually within Exchange accounts, but we can display from->to if you prefer.
      // For a simple approach, we just say "Exchange".
      // Or you can do something like:
      // return `${accountIdToName(from_account_id)} -> ${accountIdToName(to_account_id)}`;
      return "Exchange";

    default:
      return "???";
  }
}

/**
 * formatAmount:
 * We only have `amount` in the backend. For Buy/Sell, we also have `cost_basis_usd` or `proceeds_usd`.
 * We'll adapt the old logic to the new structure:
 *  - For deposit/withdrawal/transfer, show `amount`, possibly with the currency context.
 *  - For buy: show "USD spent -> ??? BTC" if you want. But the new backend doesn't store how many BTC were purchased,
 *    unless you stored it somewhere else. We'll just display the `amount` as the from side plus any cost_basis_usd.
 *  - For sell: show "BTC sold -> $proceeds_usd" if you want.
 */
function formatAmount(tx: ITransaction): string {
  const { type, amount, cost_basis_usd, proceeds_usd } = tx;

  switch (type) {
    case "Deposit":
    case "Withdrawal":
    case "Transfer":
      // For these, the new backend only keeps a single `amount`.
      // If you want to guess USD vs. BTC, you can do so by checking from_account_id or to_account_id.
      return `${amount}`;

    case "Buy":
      // from=ExchangeUSD => `amount` is the USD spent
      // If cost_basis_usd is set, it usually equals the amount
      // We don't store how many BTC in the new backend unless you added a field for it.
      // So let's display: "Buy: $100" (or cost_basis_usd) if you prefer
      return cost_basis_usd
        ? `$${cost_basis_usd} spent`
        : `$${amount} spent`;

    case "Sell":
      // from=ExchangeBTC => `amount` is the BTC sold
      // If proceeds_usd is set, that's the USD gained
      return proceeds_usd
        ? `Sold ${amount} BTC -> $${proceeds_usd}`
        : `Sold ${amount} BTC`;

    default:
      return `${amount}`;
  }
}

/**
 * formatExtra:
 * - For Deposit => show 'source' if not "N/A".
 * - For Withdrawal => show 'purpose' if not "N/A".
 * - You could also display cost_basis_usd or proceeds_usd if relevant.
 */
function formatExtra(tx: ITransaction): string {
  const { type, source, purpose } = tx;

  if (type === "Deposit" && source && source !== "N/A") {
    return source;
  }
  if (type === "Withdrawal" && purpose && purpose !== "N/A") {
    return purpose;
  }

  return "";
}

const Transactions: React.FC = () => {
  // State to manage the TransactionPanel (open/close)
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  // All transactions fetched from backend
  const [transactions, setTransactions] = useState<ITransaction[]>([]);

  // Sorting mode
  const [sortMode, setSortMode] = useState<SortMode>("TIMESTAMP_DESC");

  // Loading & error states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * fetchTransactions:
   * Retrieves all transactions from the new backend,
   * which now returns single `amount`, plus optional cost_basis_usd, proceeds_usd, etc.
   */
  async function fetchTransactions() {
    setLoading(true);
    setError(null);
    try {
      // Assuming the new endpoint is still GET /api/transactions
      const res = await axios.get<ITransaction[]>("http://127.0.0.1:8000/api/transactions/");
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

  /**
   * When a new transaction is submitted from TransactionPanel,
   * close the panel and refresh the list.
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
      // Sort by timestamp descending
      return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
    } else {
      // "CREATION_DESC" => sort by descending ID
      return b.id - a.id;
    }
  });

  /**
   * Group by date (YYYY-MM-DD)
   */
  const groupedByDate: Record<string, ITransaction[]> = {};
  for (const tx of sortedTransactions) {
    // Format date as "MMM DD, YYYY" or any style you like
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
      {/* Button to open panel for adding a new transaction */}
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

      {/* Loading & Error messages */}
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
                const timeStr = new Date(tx.timestamp).toLocaleTimeString("en-US", {
                  hour: "numeric",
                  minute: "2-digit",
                });

                const accountLabel = resolveDisplayAccount(tx);
                const amountLabel = formatAmount(tx);

                // If your new backend has "fee_amount" and "fee_currency" instead of "fee",
                // adapt how you display fees. For now, let's do:
                const feeNumber = tx.fee_amount ?? 0;
                const feeLabel =
                  feeNumber !== 0
                    ? `Fee: ${feeNumber} ${tx.fee_currency || "USD"}` // fallback to USD if unknown
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
                    {/* 
                      Columns:
                      1) Time
                      2) Type
                      3) Account label
                      4) Amount
                      5) Fee
                      6) Extra info
                      7) Edit button
                    */}
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

      {/* The sliding TransactionPanel for adding new transactions */}
      <TransactionPanel
        isOpen={isPanelOpen}
        onClose={closePanel}
        onSubmitSuccess={handleSubmitSuccess}
      />
    </div>
  );
};

export default Transactions;
