import React, { useEffect, useState } from "react";
import TransactionPanel from "../components/TransactionPanel";
import "../styles/transactions.css";
import api from "../api";
import {
  parseTransaction,
  formatUsd,
  formatBtc,
  formatTimestamp,
  parseDecimal,
} from "../utils/format";

// IMPORTANT:
// Because `global.d.ts` declares ITransaction, ITransactionRaw, SortMode, etc. 
// in the global scope, we do NOT import them here.
// We can just use `ITransaction`, `ITransactionRaw`, etc., directly.

void formatTimestamp; // to avoid TS “unused import” warnings
void parseDecimal;    // same reason

// ----------------------------------------------------
// Utility function to map account IDs to names
// ----------------------------------------------------
function accountIdToName(id: number | null): string {
  if (id === null) return "N/A";
  switch (id) {
    case 1:
      return "Bank";
    case 2:
      return "Wallet";
    case 3:
      return "Exchange";
    case 4:
      return "Exchange";
    case 99:
      return "External";
    default:
      return `Acct #${id}`;
  }
}

// ----------------------------------------------------
// Decide how to display the "account" label
// ----------------------------------------------------
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
      return "Exchange";
    default:
      return "Unknown";
  }
}

// ----------------------------------------------------
// Format the "Amount" column based on transaction type
// ----------------------------------------------------
function formatAmount(tx: ITransaction): string {
  const { type, amount, cost_basis_usd, proceeds_usd, from_account_id, to_account_id } = tx;

  switch (type) {
    case "Deposit":
      // If depositing into Bank(1) or Exchange(3), show USD
      if (to_account_id === 1 || to_account_id === 3) {
        return formatUsd(amount);
      } else {
        return formatBtc(amount);
      }

    case "Withdrawal":
      // If withdrawing from Bank(1) or Exchange(3), show USD
      if (from_account_id === 1 || from_account_id === 3) {
        return formatUsd(amount);
      } else {
        return formatBtc(amount);
      }

    case "Transfer":
      // If transferring from Bank(1) or Exchange(3), show USD
      if (from_account_id === 1 || from_account_id === 3) {
        return formatUsd(amount);
      } else {
        return formatBtc(amount);
      }

    case "Buy":
      // Show "spent USD -> gained BTC"
      return cost_basis_usd
        ? `${formatUsd(cost_basis_usd)} -> ${formatBtc(amount)}`
        : `${formatUsd(amount)}`;

    case "Sell":
      // Show "spent BTC -> gained USD"
      return proceeds_usd
        ? `${formatBtc(amount)} -> ${formatUsd(proceeds_usd)}`
        : `${formatBtc(amount)}`;

    default:
      // Fallback: just show the raw amount
      return `${amount}`;
  }
}

// ----------------------------------------------------
// Format "Extra" label (e.g., deposit source or withdrawal purpose)
// ----------------------------------------------------
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

// ----------------------------------------------------
// Build disposal label for Sell/Withdrawal 
// to show Gains/Losses (and holding period)
// ----------------------------------------------------
function buildDisposalLabel(tx: ITransaction): string {
  // Only applies to Sell or Withdrawal
  if (tx.type !== "Sell" && tx.type !== "Withdrawal") return "";
  if (tx.cost_basis_usd == null || tx.realized_gain_usd == null) return "";

  const costBasis = parseDecimal(tx.cost_basis_usd);
  const gainVal = parseDecimal(tx.realized_gain_usd);
  const hp = tx.holding_period ? ` (${tx.holding_period})` : "";

  // Decide prefix: "Gain" or "Loss"
  const label = gainVal >= 0 ? "Gain" : "Loss";

  // If cost basis = 0, show just the gain/loss $ if nonzero
  if (costBasis === 0) {
    if (gainVal === 0) return "";
    const sign = gainVal >= 0 ? "+" : "-";
    return `${label}: ${sign}${formatUsd(Math.abs(gainVal))}${hp}`;
  }

  // Otherwise, show “Gain: ±$X (±YY%)” or “Loss: -$X (-YY%)”
  const gainPerc = (gainVal / costBasis) * 100;
  const sign = gainVal >= 0 ? "+" : "-";
  const absGain = Math.abs(gainVal);
  const absPerc = Math.abs(gainPerc).toFixed(2);

  return `${label}: ${sign}${formatUsd(absGain)} (${sign}${absPerc}%)${hp}`;
}

// ----------------------------------------------------
// Main Transactions Component
// ----------------------------------------------------
const Transactions: React.FC = () => {
  // Local state
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [transactions, setTransactions] = useState<ITransaction[] | null>(null);
  const [sortMode, setSortMode] = useState<SortMode>("TIMESTAMP_DESC");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  // New state for tracking the transaction being edited
  const [editingTransactionId, setEditingTransactionId] = useState<number | null>(null);

  // --------------------------------------------------
  // Fetch Transactions from the API
  // --------------------------------------------------
  const fetchTransactions = async () => {
    setIsLoading(true);
    setFetchError(null);

    try {
      // We expect an array of ITransactionRaw from the server
      const res = await api.get<ITransactionRaw[]>("/transactions");
      console.log("Raw API response (transactions):", res.data);

      // Convert raw string fields into numeric
      const parsedTransactions = res.data.map(raw => parseTransaction(raw));
      console.log("Parsed transactions:", parsedTransactions);

      setTransactions(parsedTransactions);
    } catch (err) {
      const errorMsg =
        err instanceof Error
          ? `Failed to load transactions: ${err.message}`
          : "Failed to load transactions: Unknown error";
      console.error(errorMsg, err);
      setFetchError(errorMsg);
      setTransactions(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, []);

  // --------------------------------------------------
  // Dialog toggles
  // --------------------------------------------------
  const openPanel = () => setIsPanelOpen(true);
  const closePanel = () => {
    setIsPanelOpen(false);
    setEditingTransactionId(null); // Reset editing ID when closing
  };

  // Called after a successful form submit
  const handleSubmitSuccess = () => {
    setIsPanelOpen(false);
    setEditingTransactionId(null); // Reset after successful submit
    fetchTransactions();
  };

  // --------------------------------------------------
  // Sorting
  // --------------------------------------------------
  const sortedTransactions = transactions
    ? [...transactions].sort((a, b) => {
        if (sortMode === "TIMESTAMP_DESC") {
          // Sort by date/time descending
          return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
        } else {
          // CREATION_DESC => sort by ID descending
          return b.id - a.id;
        }
      })
    : [];

  // --------------------------------------------------
  // Group by date
  // --------------------------------------------------
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

  // --------------------------------------------------
  // Render
  // --------------------------------------------------
  return (
    <div className="transactions-page">
      {/* Header row with Add button (left) and sort control (right) */}
      <div className="transactions-header">
        <button className="accent-btn" onClick={openPanel}>
          Add Transaction
        </button>

        <div className="sort-wrapper">
          <select
            className="sort-select"
            value={sortMode}
            onChange={e => setSortMode(e.target.value as SortMode)}
          >
            <option value="TIMESTAMP_DESC">Sort by Date</option>
            <option value="CREATION_DESC">Last Added (ID)</option>
          </select>
        </div>
      </div>

      {isLoading && <p>Loading transactions...</p>}

      {fetchError && (
        <div className="error-section">
          <p>{fetchError}</p>
          <button onClick={fetchTransactions} className="retry-btn">
            Retry
          </button>
        </div>
      )}

      {/* Show "No transactions" if we’re not loading/fetchError and have empty array */}
      {!isLoading && !fetchError && transactions && transactions.length === 0 && (
        <p>No transactions found.</p>
      )}

      {/* Show transactions if we have them */}
      {!isLoading && !fetchError && transactions && transactions.length > 0 && (
        <div className="transactions-list">
          {dateGroups.map(([dayLabel, txArray]) => (
            <div key={dayLabel} className="transactions-day-group">
              <h3 className="date-heading">{dayLabel}</h3>

              {/* Each transaction row */}
              {txArray.map(tx => {
                const timeStr = new Date(tx.timestamp).toLocaleTimeString("en-US", {
                  hour: "numeric",
                  minute: "2-digit",
                });

                // Determine label text
                const accountLabel = resolveDisplayAccount(tx);
                const amountLabel = formatAmount(tx);

                // If there's a fee, display it. e.g. "Fee: $5.00 USD"
                let feeLabel = "";
                if (tx.fee_amount && tx.fee_amount !== 0) {
                  feeLabel =
                    tx.fee_currency === "BTC"
                      ? `Fee: ${formatBtc(tx.fee_amount)}`
                      : `Fee: ${formatUsd(tx.fee_amount)} ${tx.fee_currency || "USD"}`;
                }

                const extraLabel = formatExtra(tx);
                const disposalLabel = buildDisposalLabel(tx);

                // We'll color the disposal label green or red based on realized gain
                const disposalColor = tx.realized_gain_usd >= 0 ? "gain-green" : "loss-red";

                return (
                  <div key={tx.id} className="transaction-card">
                    {/* Time */}
                    <span className="cell time-col">{timeStr}</span>

                    {/* Type */}
                    <span className="cell type-col">{tx.type}</span>

                    {/* Account */}
                    <span className="cell account-col">{accountLabel}</span>

                    {/* Amount */}
                    <span className="cell amount-col">{amountLabel}</span>

                    {/* Fee */}
                    <span className="cell fee-col">{feeLabel}</span>

                    {/* Extra info (e.g. "Spent", "Income", etc.) */}
                    <span className="cell extra-col">{extraLabel}</span>

                    {/* Disposal (gains/losses) */}
                    <span className={`cell disposal-col ${disposalColor}`}>
                      {disposalLabel}
                    </span>

                    {/* Edit button pinned on the right */}
                    <button
                      onClick={() => {
                        setEditingTransactionId(tx.id);
                        setIsPanelOpen(true);
                      }}
                      className="edit-button"
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

      {/* Slide‐in panel for adding a new transaction */}
      <TransactionPanel
        isOpen={isPanelOpen}
        onClose={closePanel}
        onSubmitSuccess={handleSubmitSuccess}
        transactionId={editingTransactionId} // Pass the ID to the panel
      />
    </div>
  );
};

export default Transactions;
