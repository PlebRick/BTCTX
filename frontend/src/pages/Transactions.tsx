/**
 * Transactions.tsx
 *
 * This page displays a list of all transactions in a table format.
 * It uses the TransactionRead data from the backend, which now includes
 * both from_account_id and to_account_id along with new tax fields.
 * The UI maps account IDs to human-readable names and shows key details.
 */

import React, { useEffect, useState } from "react";
import axios from "axios";
import "../styles/transactions.css";

// Define the Transaction interface based on our backend schema
interface Transaction {
  id: number;
  from_account_id: number | null;
  to_account_id: number | null;
  amount: number;
  type: string;
  timestamp: string;
  cost_basis_usd?: number;
  proceeds_usd?: number;
  realized_gain_usd?: number;
  holding_period?: string;
  fee_amount?: number;
  fee_currency?: string;
  external_ref?: string;
  group_id?: number | null;
}

// A simple mapping of account IDs to names for display purposes (assumes fixed IDs)
function accountIdToName(id: number | null): string {
  const mapping: Record<number, string> = {
    1: "Bank",
    2: "Wallet",
    3: "Exchange (USD)",
    4: "Exchange (BTC)",
    5: "External"
  };
  return id && mapping[id] ? mapping[id] : "Unknown";
}

// Resolve display string for a transaction
function resolveAccountDisplay(tx: Transaction): string {
  // For a deposit: show "External -> {to_account}"
  // For a withdrawal: show "{from_account} -> External"
  // For transfer/trade: show "{from_account} -> {to_account}"
  if (tx.type.toUpperCase() === "DEPOSIT") {
    return `External -> ${accountIdToName(tx.to_account_id)}`;
  }
  if (tx.type.toUpperCase() === "WITHDRAWAL") {
    return `${accountIdToName(tx.from_account_id)} -> External`;
  }
  // For transfers, buys, and sells:
  return `${accountIdToName(tx.from_account_id)} -> ${accountIdToName(tx.to_account_id)}`;
}

const Transactions: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);

  // Fetch transactions on component mount
  useEffect(() => {
    axios.get("http://127.0.0.1:8000/transactions/")
      .then(response => setTransactions(response.data))
      .catch(error => console.error("Error fetching transactions:", error));
  }, []);

  return (
    <div className="transactions-page">
      <h1>Transaction History</h1>
      <table className="transactions-table">
        <thead>
          <tr>
            <th>Date/Time</th>
            <th>Type</th>
            <th>Accounts</th>
            <th>Amount</th>
            <th>Cost Basis (USD)</th>
            <th>Realized Gain (USD)</th>
            <th>Holding Period</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map(tx => (
            <tr key={tx.id}>
              <td>{new Date(tx.timestamp).toLocaleString()}</td>
              <td>{tx.type}</td>
              <td>{resolveAccountDisplay(tx)}</td>
              <td>{tx.amount}</td>
              <td>{tx.cost_basis_usd !== null ? `$${tx.cost_basis_usd}` : "-"}</td>
              <td>{tx.realized_gain_usd !== null ? `$${tx.realized_gain_usd}` : "-"}</td>
              <td>{tx.holding_period || "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Transactions;
