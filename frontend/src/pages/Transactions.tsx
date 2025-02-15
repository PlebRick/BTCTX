// src/pages/Transactions.tsx

import React, { useEffect, useState } from "react";
import axios from "axios";
import TransactionPanel from "../components/TransactionPanel";
import '../styles/transactions.css';

// Example transaction interface (or import from a types folder)
interface ITransaction {
  id: number;
  account_id: number;
  type: "Deposit" | "Withdrawal" | "Transfer" | "Buy" | "Sell";
  amount_usd: number;
  amount_btc: number;
  timestamp: string; 
  source: string;
  purpose: string;
  fee: number;
  cost_basis_usd: number;
  is_locked: boolean;
}

type SortMode = "TIMESTAMP_DESC" | "CREATION_DESC";

const Transactions: React.FC = () => {
  // Controls the sliding panel
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  // Transaction data from backend
  const [transactions, setTransactions] = useState<ITransaction[]>([]);
  const [sortMode, setSortMode] = useState<SortMode>("TIMESTAMP_DESC");

  // Loading & error state
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // ------------------------------------------------------------
  // Fetch transactions from your backend
  // ------------------------------------------------------------
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

  // ------------------------------------------------------------
  // Open/Close the panel
  // ------------------------------------------------------------
  const openPanel = () => setIsPanelOpen(true);
  const closePanel = () => setIsPanelOpen(false);

  // Called after a new transaction is submitted
  const handleSubmitSuccess = () => {
    // close panel, then reload transactions
    setIsPanelOpen(false);
    fetchTransactions();
  };

  // ------------------------------------------------------------
  // Sorting
  // ------------------------------------------------------------
  const sortedTransactions = [...transactions].sort((a, b) => {
    if (sortMode === "TIMESTAMP_DESC") {
      return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
    } else {
      return b.id - a.id;
    }
  });

  // ------------------------------------------------------------
  // Group by date (e.g., "Feb 15, 2025")
  // ------------------------------------------------------------
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

  // ------------------------------------------------------------
  // Render
  // ------------------------------------------------------------
  return (
    <div className="transactions-page" style={{ padding: "1rem" }}>

      {/* Add Transaction button */}
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

      {/* Loading / Error / No items */}
      {loading && <p>Loading transactions...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
      {!loading && !error && dateGroups.length === 0 && (
        <p>No transactions found.</p>
      )}

      {/* Transaction listing */}
      {!loading && !error && dateGroups.length > 0 && (
        <div className="transactions-list" style={{ marginTop: "1rem" }}>
          {dateGroups.map(([dayLabel, txArray]) => (
            <div key={dayLabel} className="transactions-day-group" style={{ marginBottom: "1rem" }}>
              <h3>{dayLabel}</h3>
              {txArray.map((tx) => {
                const timeStr = new Date(tx.timestamp).toLocaleTimeString(
                  "en-US",
                  { hour: "numeric", minute: "2-digit" }
                );

                return (
                  <div
                    key={tx.id}
                    className="transaction-card"
                    style={{
                      backgroundColor: "#1b1b1b",
                      color: "#fff",
                      padding: "0.5rem 1rem",
                      marginBottom: "0.5rem",
                      borderRadius: "4px",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <div>
                        <strong>{tx.type}</strong> - {timeStr}
                      </div>
                      <button
                        onClick={() => {
                          // TODO: handle edit logic -> open panel in edit mode
                          console.log("Edit transaction", tx.id);
                        }}
                      >
                        Edit
                      </button>
                    </div>
                    <div>
                      {tx.amount_usd !== 0 && (
                        <span style={{ marginRight: "1rem" }}>
                          {tx.amount_usd > 0 ? "+" : "-"}${Math.abs(tx.amount_usd)}
                        </span>
                      )}
                      {tx.amount_btc !== 0 && (
                        <span style={{ marginRight: "1rem" }}>
                          {tx.amount_btc > 0 ? "+" : "-"}
                          {Math.abs(tx.amount_btc)} BTC
                        </span>
                      )}
                      {tx.fee !== 0 && <span>Fee: ${tx.fee}</span>}
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      )}

      {/* Sliding Panel: pass onSubmitSuccess */}
      <TransactionPanel
        isOpen={isPanelOpen}
        onClose={closePanel}
        onSubmitSuccess={handleSubmitSuccess}
      />
    </div>
  );
};

export default Transactions;