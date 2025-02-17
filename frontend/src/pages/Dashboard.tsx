/**
 * Dashboard.tsx
 *
 * This component displays the account balances and portfolio summary,
 * including real-time updates of realized and unrealized gains.
 * It fetches data from the backend summary endpoint.
 *
 * The dashboard shows separate lines/cards for Bank, Wallet, Exchange (USD), and Exchange (BTC)
 * so the user can clearly see each account's balance.
 */

import React, { useEffect, useState } from "react";
import axios from "axios";
import "../styles/dashboard.css";

// Define interface for account data (simplified)
interface Account {
  id: number;
  name: string;
  currency: string;
  balance: number;
}

// Interface for summary response
interface PortfolioSummary {
  total_realized_usd: number;
  total_unrealized_usd: number;
}

const Dashboard: React.FC = () => {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);

  // Fetch accounts and portfolio summary on component mount
  useEffect(() => {
    axios.get("http://127.0.0.1:8000/accounts/")
      .then(response => setAccounts(response.data))
      .catch(error => console.error("Error fetching accounts:", error));

    axios.get("http://127.0.0.1:8000/dashboard/summary")
      .then(response => setSummary(response.data))
      .catch(error => console.error("Error fetching summary:", error));
  }, []);

  return (
    <div className="dashboard">
      <h1>Portfolio Dashboard</h1>
      <div className="accounts-section">
        {accounts.map(account => (
          <div key={account.id} className="account-card">
            <h3>{account.name}</h3>
            <p>{account.currency === "USD" ? "$" : "₿"}{account.balance}</p>
          </div>
        ))}
      </div>
      {summary && (
        <div className="summary-section">
          <h2>Realized Gain: ${summary.total_realized_usd}</h2>
          <h2>Unrealized Gain: ${summary.total_unrealized_usd}</h2>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
