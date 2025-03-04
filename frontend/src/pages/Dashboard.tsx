/**
 * Dashboard.tsx
 *
 * Shows aggregated balances & gains/losses. Uses globally defined types:
 * - AccountBalance
 * - GainsAndLosses
 * - GainsAndLossesRaw
 * for typed state management and fetch handling.
 *
 * Updated to:
 *  - Exclude fee accounts from main portfolio balances
 *  - Use `parseGainsAndLosses` from `format.ts` for GainsAndLosses parsing
 */

import React, { useEffect, useState } from "react";
import api from "../api"; // Centralized API client
import "../styles/dashboard.css";

// Numeric helpers
import {
  parseDecimal,
  formatUsd,
  formatBtc,
  parseGainsAndLosses, // <-- We'll use this helper function
} from "../utils/format";

const Dashboard: React.FC = () => {
  // -----------------------------
  // State for Account Balances
  // -----------------------------
  const [balances, setBalances] = useState<AccountBalance[] | null>(null);

  // Individual “named” account balances
  const [bankBalance, setBankBalance] = useState<number>(0);
  const [exchangeUSDBalance, setExchangeUSDBalance] = useState<number>(0);
  const [exchangeBTCBalance, setExchangeBTCBalance] = useState<number>(0);
  const [walletBTCBalance, setWalletBTCBalance] = useState<number>(0);

  // Totals for the entire portfolio
  const [totalBTC, setTotalBTC] = useState<number>(0);
  const [totalUSD, setTotalUSD] = useState<number>(0);

  // -----------------------------
  // Gains & Losses
  // -----------------------------
  const [gainsAndLosses, setGainsAndLosses] = useState<GainsAndLosses | null>(null);

  // General error handling
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Placeholder for unrealized gains
  const unrealizedGains = 0; // If not provided by backend, we leave it as 0

  // -----------------------------
  // 1) Fetch account balances
  // -----------------------------
  useEffect(() => {
    api
      .get("/calculations/accounts/balances")
      .then((response) => {
        const data = response.data;
        console.log("Fetched balances data:", data);

        if (!Array.isArray(data)) {
          throw new Error(
            "Data is not an array. Received: " + JSON.stringify(data)
          );
        }
        setBalances(data as AccountBalance[]);
      })
      .catch((err) => {
        console.error("Error fetching balances:", err);
        setFetchError(String(err));
      });
  }, []);

  /**
   * Process fetched balances into local state, skipping fee accounts
   * to avoid inflating the user's main BTC or USD totals.
   */
  useEffect(() => {
    if (!balances) return;

    let bank = 0;
    let exchUSD = 0;
    let exchBTC = 0;
    let walletBTC = 0;

    let totalBtcTemp = 0;
    let totalUsdTemp = 0;

    // Loop over balances and filter out fee accounts by skipping them
    balances.forEach((acc) => {
      // We parse the string|number balance to a number
      const numericBalance = parseDecimal(acc.balance);
      if (Number.isNaN(numericBalance)) {
        console.warn("Encountered NaN balance for account:", acc);
        return;
      }

      // Skip if this account is a fee account
      if (acc.name === "BTC Fees" || acc.name === "USD Fees") {
        return;
      }

      // Identify known non-fee accounts by name/currency
      if (acc.name === "Bank" && acc.currency === "USD") {
        bank = numericBalance;
      } else if (acc.name === "Wallet" && acc.currency === "BTC") {
        walletBTC = numericBalance;
      } else if (acc.name === "Exchange USD" && acc.currency === "USD") {
        exchUSD = numericBalance;
      } else if (acc.name === "Exchange BTC" && acc.currency === "BTC") {
        exchBTC = numericBalance;
      }

      // Tally total BTC / USD for main accounts only (no fees)
      if (acc.currency === "BTC") {
        totalBtcTemp += numericBalance;
      } else if (acc.currency === "USD") {
        totalUsdTemp += numericBalance;
      }
    });

    // Update state with final sums
    setBankBalance(bank);
    setExchangeUSDBalance(exchUSD);
    setExchangeBTCBalance(exchBTC);
    setWalletBTCBalance(walletBTC);

    setTotalBTC(totalBtcTemp);
    setTotalUSD(totalUsdTemp);
  }, [balances]);

  // -----------------------------
  // 2) Fetch Gains and Losses
  // -----------------------------
  useEffect(() => {
    api
      .get<GainsAndLossesRaw>("/calculations/gains-and-losses")
      .then((response) => {
        console.log("Fetched gains and losses data:", response.data);

        // Use parseGainsAndLosses for numeric conversion
        const parsed = parseGainsAndLosses(response.data);
        setGainsAndLosses(parsed);
      })
      .catch((err) => {
        console.error("Error fetching gains and losses:", err);
        setFetchError(String(err));
      });
  }, []);

  // For converting BTC-based fees (or other BTC amounts) to USD
  // until you fetch a live price:
  const BTC_PRICE = 25000; // example only

  // -----------------------------
  // Render logic (handle errors/loading)
  // -----------------------------
  if (fetchError) {
    return (
      <div style={{ color: "red", margin: "2rem" }}>
        <h2>Error Loading Data</h2>
        <p>{fetchError}</p>
      </div>
    );
  }

  // If either call is still loading, show a basic loading state
  if (balances === null || gainsAndLosses === null) {
    return (
      <div className="dashboard">
        <h2>Loading data...</h2>
      </div>
    );
  }

  // Compute total fees in USD by converting BTC fees at a placeholder price
  const totalFeesUsd =
    gainsAndLosses.fees.USD + gainsAndLosses.fees.BTC * BTC_PRICE;

  return (
    <div className="dashboard">
      {/* -------------------- TOP ROW -------------------- */}
      <div className="dashboard-row top-row">
        {/* Portfolio Card */}
        <div className="card">
          <h5>Portfolio</h5>
          <p>BTC Balance: {formatBtc(totalBTC)}</p>
          <p>USD Value: {formatUsd(totalUSD)}</p>
          <p>Unrealized Gains/Losses: {unrealizedGains}</p>
          <p>Portfolio Chart: (Placeholder)</p>
        </div>

        {/* BTC Price Card */}
        <div className="card">
          <h5>Bitcoin Price</h5>
          <p>Placeholder for live BTC price & chart</p>
        </div>
      </div>

      {/* -------------------- BOTTOM ROW: ACCOUNTS -------------------- */}
      <div className="dashboard-row bottom-row">
        {/* Bank */}
        <div className="card">
          <h5>Bank</h5>
          <p>USD Balance: {formatUsd(bankBalance)}</p>
        </div>

        {/* Exchange */}
        <div className="card">
          <h5>Exchange</h5>
          <p>USD Balance: {formatUsd(exchangeUSDBalance)}</p>
          <p>BTC Balance: {formatBtc(exchangeBTCBalance)}</p>
        </div>

        {/* Wallet */}
        <div className="card">
          <h5>Wallet</h5>
          <p>BTC Balance: {formatBtc(walletBTCBalance)}</p>
        </div>
      </div>

      {/* -------------------- GAINS & LOSSES ROW -------------------- */}
      <div className="dashboard-row bottom-row">
        {/* Realized Gains */}
        <div className="card">
          <h5>Realized Gains</h5>
          {/* If you do short-term vs. long-term, you’ll need them from the backend. */}
          <p>Short term: N/A</p>
          <p>Long term: N/A</p>
          {/* Actual net gains in total */}
          <p>Total Gains: {formatUsd(gainsAndLosses.total_gains)}</p>
        </div>

        {/* Other Gains */}
        <div className="card">
          <h5>Other Gains</h5>
          <p>Proceeds from Sells: {formatUsd(gainsAndLosses.sells_proceeds)}</p>
          <p>Income: {formatUsd(gainsAndLosses.income_earned)}</p>
          <p>Interest: {formatUsd(gainsAndLosses.interest_earned)}</p>
          <p>Spent (on Withdrawals): {formatUsd(gainsAndLosses.withdrawals_spent)}</p>
        </div>

        {/* Losses */}
        <div className="card">
          <h5>Losses</h5>
          <p>Short term: N/A</p>
          <p>Long term: N/A</p>
          <p>Total: {formatUsd(gainsAndLosses.total_losses)}</p>
        </div>

        {/* Fees */}
        <div className="card">
          <h5>Fees</h5>
          <p>Fees (USD): {formatUsd(gainsAndLosses.fees.USD)}</p>
          <p>Fees (BTC): {formatBtc(gainsAndLosses.fees.BTC)}</p>
          <p>Total Fees in USD (approx): {formatUsd(totalFeesUsd)}</p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
