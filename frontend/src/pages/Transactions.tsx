/**
 * Transactions.tsx
 *
 * A page that lists all transactions. We previously defined:
 *   - ITransactionRaw
 *   - ITransaction
 *   - SortMode
 * in global.d.ts. Now we remove local interfaces & rely on the global.
 */

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

void formatTimestamp; // Just to avoid TS unused warnings
void parseDecimal;    // Same reason

/**
 * Convert numeric account ID => label (UI only)
 */
function accountIdToName(id: number | null): string {
  if (id === null) return "N/A";
  switch (id) {
    case 1: return "Bank";
    case 2: return "Wallet";
    case 3: return "Exchange";
    case 4: return "Exchange";
    case 99: return "External";
    default: return `Acct #${id}`;
  }
}

/**
 * Decide how to display the "main" account or direction of the transaction
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
      return "Exchange";
    default:
      return "Unknown";
  }
}

/**
 * Decide how to display the primary amount (or a short phrase).
 */
function formatAmount(tx: ITransaction): string {
  const { type, amount, cost_basis_usd, proceeds_usd, from_account_id, to_account_id } = tx;

  switch (type) {
    case "Deposit":
      if (to_account_id === 1 || to_account_id === 3) {
        return formatUsd(amount);
      } else {
        return formatBtc(amount);
      }

    case "Withdrawal":
      if (from_account_id === 1 || from_account_id === 3) {
        return formatUsd(amount);
      } else {
        return formatBtc(amount);
      }

    case "Transfer":
      if (from_account_id === 1 || from_account_id === 3) {
        return formatUsd(amount);
      } else {
        return formatBtc(amount);
      }

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
 * For deposits, we show 'source'; for withdrawals, 'purpose'; for Sell or Disposal,
 * we might show holding_period, but let's keep it separate. We'll add an additional
 * label for gain/loss.
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

// <--- ADDED: Build a disposal label: gain/loss + % + holding period
function buildDisposalLabel(tx: ITransaction): string {
  // Only show if Sell or Withdrawal
  if (tx.type !== "Sell" && tx.type !== "Withdrawal") {
    return "";
  }
  // Must have cost_basis_usd and realized_gain_usd to be meaningful
  if (tx.cost_basis_usd == null || tx.realized_gain_usd == null) {
    return "";
  }

  const costBasis = parseDecimal(tx.cost_basis_usd);
  const gainVal   = parseDecimal(tx.realized_gain_usd);

  if (costBasis === 0) {
    // If there's no cost basis, or zero => no ratio
    // Possibly user donated or lost?
    return gainVal !== 0
      ? `Gain: ${gainVal >= 0 ? "+" : ""}${formatUsd(gainVal)}`
      : "";
  }

  const gainPerc = (gainVal / costBasis) * 100;
  const sign = gainVal >= 0 ? "+" : "";
  const percFmt = `${sign}${gainPerc.toFixed(2)}%`;
  const gainFmt = `${sign}${formatUsd(gainVal)}`;

  // If there's a holding_period, add it in parentheses
  const hp = tx.holding_period ? ` ${tx.holding_period}` : "";

  return `Gain: ${gainFmt} (${percFmt})${hp}`;
}

const Transactions: React.FC = () => {
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [transactions, setTransactions] = useState<ITransaction[] | null>(null);
  const [sortMode, setSortMode] = useState<SortMode>("TIMESTAMP_DESC");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  /**
   * Fetch transactions from backend
   */
  const fetchTransactions = async () => {
    setIsLoading(true);
    setFetchError(null);

    try {
      const res = await api.get<ITransactionRaw[]>("/transactions");
      console.log("Raw API response (transactions):", res.data);

      // parse them to unify numeric fields
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

  const openPanel = () => setIsPanelOpen(true);
  const closePanel = () => setIsPanelOpen(false);

  const handleSubmitSuccess = () => {
    setIsPanelOpen(false);
    fetchTransactions();
  };

  /**
   * Sort transactions
   */
  const sortedTransactions = transactions
    ? [...transactions].sort((a, b) => {
        if (sortMode === "TIMESTAMP_DESC") {
          return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
        } else {
          // CREATION_DESC => sort by ID descending
          return b.id - a.id;
        }
      })
    : [];

  /**
   * Group them by date string (e.g. "Mar 1, 2025")
   */
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
      <button className="accent-btn" onClick={openPanel}>
        Add Transaction
      </button>

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

      {isLoading && <p>Loading transactions...</p>}

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

      {!isLoading && !fetchError && transactions && transactions.length === 0 && (
        <p>No transactions found.</p>
      )}

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
                const accountLabel = resolveDisplayAccount(tx);
                const amountLabel = formatAmount(tx);
                let feeLabel = "";
                if (tx.fee_amount && tx.fee_amount !== 0) {
                  if (tx.fee_currency === "BTC") {
                    feeLabel = `Fee: ${formatBtc(tx.fee_amount)}`;
                  } else {
                    feeLabel = `Fee: ${formatUsd(tx.fee_amount)} ${
                      tx.fee_currency || "USD"
                    }`;
                  }
                }
                const extraLabel = formatExtra(tx);

                // <--- ADDED: Build disposal label (gain/loss) if applicable
                const disposalLabel = buildDisposalLabel(tx);

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
                    <span style={{ flex: 1 }}>
                      {extraLabel}
                      {disposalLabel && (
                        <span style={{ marginLeft: "0.8rem", color: "#bbb" }}>
                          {disposalLabel}
                        </span>
                      )}
                    </span>
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

      <TransactionPanel
        isOpen={isPanelOpen}
        onClose={closePanel}
        onSubmitSuccess={handleSubmitSuccess}
      />
    </div>
  );
};

export default Transactions;
