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

// If your global.d.ts uses global declarations, you do NOT import them:
// import { ITransactionRaw, ITransaction, SortMode } from "../global.d"; // <- remove or comment out

void formatTimestamp; // to avoid TS warnings
void parseDecimal;    // to avoid TS warnings

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
      // Just show the USD amount, no "spent"
      return cost_basis_usd
        ? `${formatUsd(cost_basis_usd)}`
        : `${formatUsd(amount)}`;

    case "Sell":
      // Show "BTC -> USD" but omit "Sold"
      return proceeds_usd
        ? `${formatBtc(amount)} -> ${formatUsd(proceeds_usd)}`
        : `${formatBtc(amount)}`;

    default:
      return `${amount}`;
  }
} // <-- IMPORTANT: closing brace for formatAmount() function

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

function buildDisposalLabel(tx: ITransaction): string {
  if (tx.type !== "Sell" && tx.type !== "Withdrawal") {
    return "";
  }
  if (tx.cost_basis_usd == null || tx.realized_gain_usd == null) {
    return "";
  }

  const costBasis = parseDecimal(tx.cost_basis_usd);
  const gainVal   = parseDecimal(tx.realized_gain_usd);

  if (costBasis === 0) {
    return gainVal !== 0
      ? `Gain: ${gainVal >= 0 ? "+" : ""}${formatUsd(gainVal)}`
      : "";
  }

  const gainPerc = (gainVal / costBasis) * 100;
  const sign = gainVal >= 0 ? "+" : "";
  const percFmt = `${sign}${gainPerc.toFixed(2)}%`;
  const gainFmt = `${sign}${formatUsd(gainVal)}`;
  const hp = tx.holding_period ? ` (${tx.holding_period})` : "";

  return `Gain: ${gainFmt} (${percFmt})${hp}`;
}

const Transactions: React.FC = () => {
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [transactions, setTransactions] = useState<ITransaction[] | null>(null);
  const [sortMode, setSortMode] = useState<SortMode>("TIMESTAMP_DESC");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const fetchTransactions = async () => {
    setIsLoading(true);
    setFetchError(null);

    try {
      const res = await api.get<ITransactionRaw[]>("/transactions");
      console.log("Raw API response (transactions):", res.data);

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

      {!isLoading && !fetchError && transactions && transactions.length === 0 && (
        <p>No transactions found.</p>
      )}

      {!isLoading && !fetchError && transactions && transactions.length > 0 && (
        <div className="transactions-list">
          {dateGroups.map(([dayLabel, txArray]) => (
            <div key={dayLabel} className="transactions-day-group">
              <h3 className="date-heading">{dayLabel}</h3>
              {txArray.map(tx => {
                const timeStr = new Date(tx.timestamp).toLocaleTimeString("en-US", {
                  hour: "numeric",
                  minute: "2-digit",
                });

                const accountLabel = resolveDisplayAccount(tx);
                const amountLabel = formatAmount(tx);

                let feeLabel = "";
                if (tx.fee_amount && tx.fee_amount !== 0) {
                  feeLabel =
                    tx.fee_currency === "BTC"
                      ? `Fee: ${formatBtc(tx.fee_amount)}`
                      : `Fee: ${formatUsd(tx.fee_amount)} ${tx.fee_currency || "USD"}`;
                }

                const extraLabel = formatExtra(tx);
                const disposalLabel = buildDisposalLabel(tx);

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
                    {/* Extra (e.g. "Interest," "Spent," "Income") */}
                    <span className="cell extra-col">{extraLabel}</span>
                    {/* Disposal (e.g. "Gain: +$123.00 (40%)") */}
                    <span className="cell disposal-col">
                      {disposalLabel}
                    </span>
                    {/* Edit button */}
                    <button
                      onClick={() => {
                        console.log("Edit transaction", tx.id);
                        alert("Edit functionality TBD");
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

      <TransactionPanel
        isOpen={isPanelOpen}
        onClose={closePanel}
        onSubmitSuccess={handleSubmitSuccess}
      />
    </div>
  );
};

export default Transactions;
