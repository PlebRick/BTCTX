import React, { useEffect, useState } from 'react';
import api from '../api'; // Centralized API client
import '../styles/dashboard.css';

// Define the interface for account balance data returned by the API.
interface AccountBalance {
  account_id: number;
  name: string;
  currency: string;
  balance: number | string; // We'll convert this to a number if it's a string.
}

// Define the interface for gains and losses data returned by the API.
interface GainsAndLosses {
  sells_proceeds: number;
  withdrawals_spent: number;
  income_earned: number;
  interest_earned: number;
  fees: {
    USD: number;
    BTC: number;
  };
  total_gains: number;
  total_losses: number;
}

const Dashboard: React.FC = () => {
  // State for account balances data.
  const [balances, setBalances] = useState<AccountBalance[] | null>(null);
  
  // Individual balances for special accounts.
  const [bankBalance, setBankBalance] = useState<number>(0);
  const [exchangeUSDBalance, setExchangeUSDBalance] = useState<number>(0);
  const [exchangeBTCBalance, setExchangeBTCBalance] = useState<number>(0);
  const [walletBTCBalance, setWalletBTCBalance] = useState<number>(0);
  
  // Totals for the portfolio summary.
  const [totalBTC, setTotalBTC] = useState<number>(0);
  const [totalUSD, setTotalUSD] = useState<number>(0);
  
  // State for gains and losses calculations.
  const [gainsAndLosses, setGainsAndLosses] = useState<GainsAndLosses | null>(null);

  // State for any fetch errors.
  const [fetchError, setFetchError] = useState<string | null>(null);

  // -----------------------------
  // Fetch Account Balances
  // -----------------------------
  useEffect(() => {
    // Fetch account balances from our calculation API endpoint.
    api.get('/calculations/accounts/balances') // Fixed path: removed redundant 'api/' prefix
      .then((response) => {
        const data = response.data;
        console.log('Fetched balances data:', data);
        if (!Array.isArray(data)) {
          throw new Error('Data is not an array. Received: ' + JSON.stringify(data));
        }
        setBalances(data as AccountBalance[]);
      })
      .catch((err) => {
        console.error('Error fetching balances:', err);
        setFetchError(String(err));
      });
  }, []);

  // Process the fetched account balances to extract special accounts and totals.
  useEffect(() => {
    if (!balances) return;

    let bank = 0;
    let exchUSD = 0;
    let exchBTC = 0;
    let walletBTC = 0;
    let totalBtcTemp = 0;
    let totalUsdTemp = 0;

    balances.forEach((acc) => {
      // Convert the balance to a number if it's a string.
      const numericBalance =
        typeof acc.balance === 'string' ? parseFloat(acc.balance) : acc.balance;

      if (Number.isNaN(numericBalance)) {
        console.warn('Encountered NaN balance for account:', acc);
        return;
      }

      // Identify special accounts based on name and currency.
      if (acc.name === 'Bank' && acc.currency === 'USD') {
        bank = numericBalance;
      } else if (acc.name === 'Wallet' && acc.currency === 'BTC') {
        walletBTC = numericBalance;
      } else if (acc.name === 'Exchange USD' && acc.currency === 'USD') {
        exchUSD = numericBalance;
      } else if (acc.name === 'Exchange BTC' && acc.currency === 'BTC') {
        exchBTC = numericBalance;
      }

      // Accumulate totals for the portfolio.
      if (acc.currency === 'BTC') {
        totalBtcTemp += numericBalance;
      } else if (acc.currency === 'USD') {
        totalUsdTemp += numericBalance;
      }
    });

    setBankBalance(bank);
    setExchangeUSDBalance(exchUSD);
    setExchangeBTCBalance(exchBTC);
    setWalletBTCBalance(walletBTC);
    setTotalBTC(totalBtcTemp);
    setTotalUSD(totalUsdTemp);
  }, [balances]);

  // -----------------------------
  // Fetch Gains and Losses Calculations
  // -----------------------------
  useEffect(() => {
    // Fetch gains and losses data from our calculation API endpoint.
    api.get('/calculations/gains-and-losses') // Fixed path: removed redundant 'api/' prefix
      .then((response) => {
        const data = response.data;
        console.log('Fetched gains and losses data:', data);
        setGainsAndLosses(data as GainsAndLosses);
      })
      .catch((err) => {
        console.error('Error fetching gains and losses:', err);
        setFetchError(String(err));
      });
  }, []);

  // -----------------------------
  // Define placeholders for values not computed here.
  // For instance, unrealized gains and portfolio chart are still placeholders.
  // -----------------------------
  const unrealizedGains = 0;
  const portfolioChartPlaceholder = '(Chart Placeholder)';

  // -----------------------------
  // Display error if fetching fails.
  // -----------------------------
  if (fetchError) {
    return (
      <div style={{ color: 'red', margin: '2rem' }}>
        <h2>Error Loading Data</h2>
        <p>{fetchError}</p>
      </div>
    );
  }

  // -----------------------------
  // Display a loading state while data is being fetched.
  // -----------------------------
  if (balances === null || gainsAndLosses === null) {
    return (
      <div className="dashboard">
        <h2>Loading data...</h2>
      </div>
    );
  }

  // -----------------------------
  // Render the Dashboard with the fetched data.
  // -----------------------------
  return (
    <div className="dashboard">
      {/* Top row with Portfolio and Bitcoin Price */}
      <div className="dashboard-row top-row">
        <div className="card">
          <h5>Portfolio</h5>
          {/* Display total BTC and USD from all accounts */}
          <p>BTC Balance: {totalBTC.toFixed(4)} BTC</p>
          <p>USD Value: ${totalUSD.toFixed(2)}</p>
          <p>Unrealized Gains/Losses: {unrealizedGains}</p>
          <p>Portfolio Chart: {portfolioChartPlaceholder}</p>
        </div>
        <div className="card">
          <h5>Bitcoin Price</h5>
          <p>Placeholder for live BTC price & chart</p>
        </div>
      </div>

      {/* Bottom row with three cards for individual account balances */}
      <div className="dashboard-row bottom-row">
        <div className="card">
          <h5>Bank</h5>
          <p>USD Balance: ${bankBalance.toFixed(2)}</p>
        </div>
        <div className="card">
          <h5>Exchange</h5>
          <p>USD Balance: ${exchangeUSDBalance.toFixed(2)}</p>
          <p>BTC Balance: {exchangeBTCBalance.toFixed(4)} BTC</p>
        </div>
        <div className="card">
          <h5>Wallet</h5>
          <p>BTC Balance: {walletBTCBalance.toFixed(4)} BTC</p>
        </div>
      </div>

      {/* New row for Gains and Losses calculations */}
      <div className="dashboard-row bottom-row">
        {/* Container 1: Realized Gains (under Bank) */}
        <div className="card">
          <h5>Realized Gains</h5>
          {/* Since our API does not split into short and long term yet, we use placeholders */}
          <p>Short term: N/A</p>
          <p>Long term: N/A</p>
          <p>Total: ${gainsAndLosses.sells_proceeds.toFixed(2)}</p>
        </div>
        {/* Container 2: Other Gains (under Exchange) */}
        <div className="card">
          <h5>Other Gains</h5>
          <p>Income: ${gainsAndLosses.income_earned.toFixed(2)}</p>
          <p>Interest: ${gainsAndLosses.interest_earned.toFixed(2)}</p>
          <p>Spent: ${gainsAndLosses.withdrawals_spent.toFixed(2)}</p>
        </div>
        {/* Container 3: Losses (under Wallet) */}
        <div className="card">
          <h5>Losses</h5>
          <p>Short term: N/A</p>
          <p>Long term: N/A</p>
          <p>Total: ${gainsAndLosses.total_losses.toFixed(2)}</p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
