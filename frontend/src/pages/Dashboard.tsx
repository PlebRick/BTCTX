/**
 * Dashboard.tsx
 *
 * New layout:
 *  - Top row: 
 *    (1) Portfolio Overview (left) 
 *    (2) BTC Price Chart (right)
 *  - Bottom row side by side:
 *    (A) Account Balances
 *    (B) Realized Gains
 *    (C) Income / Interest / Rewards / Fees
 *
 * We preserve all the same data-fetching:
 *  - /calculations/accounts/balances
 *  - /calculations/gains-and-losses
 * but rearrange the UI sections.
 */

import React, { useEffect, useState } from "react";
import api from "../api"; // Centralized API client
import "../styles/dashboard.css";

// Numeric helpers
import {
  parseDecimal,
  formatUsd,
  formatBtc,
  parseGainsAndLosses,
} from "../utils/format";

const Dashboard: React.FC = () => {
  // -----------------------------
  // State for Account Balances
  // -----------------------------
  const [balances, setBalances] = useState<AccountBalance[] | null>(null);

  // For known accounts (no fee accounts)
  const [bankBalance, setBankBalance] = useState<number>(0);
  const [exchangeUSDBalance, setExchangeUSDBalance] = useState<number>(0);
  const [exchangeBTCBalance, setExchangeBTCBalance] = useState<number>(0);
  const [walletBTCBalance, setWalletBTCBalance] = useState<number>(0);

  // Totals for entire portfolio
  const [totalBTC, setTotalBTC] = useState<number>(0);
  const [totalUSD, setTotalUSD] = useState<number>(0);

  // -----------------------------
  // Gains & Losses
  // -----------------------------
  const [gainsAndLosses, setGainsAndLosses] = useState<GainsAndLosses | null>(null);

  // Basic error handling
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Placeholder for now
  const unrealizedGains = 0; // We'll do a real calculation later

  // Example BTC price for fee conversions or placeholders
  const BTC_PRICE = 25000;

  // -------------------------------------------------------
  // 1) Fetch account balances
  // -------------------------------------------------------
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
   * Process fetched balances, skipping fee accounts
   */
  useEffect(() => {
    if (!balances) return;

    let bank = 0;
    let exchUSD = 0;
    let exchBTC = 0;
    let wBTC = 0;

    let totalBtcTemp = 0;
    let totalUsdTemp = 0;

    balances.forEach((acc) => {
      const numericBalance = parseDecimal(acc.balance);
      if (Number.isNaN(numericBalance)) {
        console.warn("NaN balance for account:", acc);
        return;
      }

      // Skip fee accounts
      if (acc.name === "BTC Fees" || acc.name === "USD Fees") {
        return;
      }

      // Identify known accounts
      if (acc.name === "Bank" && acc.currency === "USD") {
        bank = numericBalance;
      } else if (acc.name === "Wallet" && acc.currency === "BTC") {
        wBTC = numericBalance;
      } else if (acc.name === "Exchange USD" && acc.currency === "USD") {
        exchUSD = numericBalance;
      } else if (acc.name === "Exchange BTC" && acc.currency === "BTC") {
        exchBTC = numericBalance;
      }

      // Tally total BTC / USD
      if (acc.currency === "BTC") {
        totalBtcTemp += numericBalance;
      } else if (acc.currency === "USD") {
        totalUsdTemp += numericBalance;
      }
    });

    // Update state
    setBankBalance(bank);
    setExchangeUSDBalance(exchUSD);
    setExchangeBTCBalance(exchBTC);
    setWalletBTCBalance(wBTC);

    setTotalBTC(totalBtcTemp);
    setTotalUSD(totalUsdTemp);
  }, [balances]);

  // -------------------------------------------------------
  // 2) Fetch Gains and Losses
  // -------------------------------------------------------
  useEffect(() => {
    api
      .get<GainsAndLossesRaw>("/calculations/gains-and-losses")
      .then((response) => {
        console.log("Fetched gains/losses:", response.data);
        const parsed = parseGainsAndLosses(response.data);
        setGainsAndLosses(parsed);
      })
      .catch((err) => {
        console.error("Error fetching gains & losses:", err);
        setFetchError(String(err));
      });
  }, []);

  // -------------------------------------------------------
  // Basic error/loading states
  // -------------------------------------------------------
  if (fetchError) {
    return (
      <div style={{ color: "red", margin: "2rem" }}>
        <h2>Error Loading Data</h2>
        <p>{fetchError}</p>
      </div>
    );
  }

  if (balances === null || gainsAndLosses === null) {
    return (
      <div className="dashboard">
        <h2>Loading data...</h2>
      </div>
    );
  }

  // Compute total fees in USD
  const totalFeesUsd =
    gainsAndLosses.fees.USD + gainsAndLosses.fees.BTC * BTC_PRICE;

  // -------------------------------------------------------
  // Render the new layout
  // -------------------------------------------------------
  return (
    <div className="dashboard">
      {/* =================== TOP ROW =================== */}
      <div className="top-row">
        {/* Left: Portfolio Overview */}
        <div className="card portfolio-overview">
          <h3>Portfolio Overview</h3>
          <p>BTC Balance: {formatBtc(totalBTC)}</p>
          <p>USD Balance: {formatUsd(totalUSD)}</p>
          <p>Unrealized Gains/Losses: {unrealizedGains}</p>

          {/* Example placeholder for line chart of user’s BTC holdings */}
          <div className="portfolio-chart-placeholder">
            <p>Portfolio Holdings Chart (Placeholder)</p>
          </div>
        </div>

        {/* Right: BTC Price Chart */}
        <div className="card btc-price-container">
          <h3>Bitcoin Price</h3>
          <p>
            Current Price (Example): <strong>${BTC_PRICE.toFixed(2)}</strong>
          </p>

          {/* Another placeholder for a chart of the live BTC price */}
          <div className="btc-price-chart-placeholder">
            <p>Live BTC Price Chart (Placeholder)</p>
          </div>
        </div>
      </div>

      {/* =================== BOTTOM ROW =================== */}
      <div className="bottom-row">
        {/* (A) Account Balances */}
        <div className="card account-balances-container">
          <h3>Account Balances</h3>
          <ul>
            <li>Bank (USD): {formatUsd(bankBalance)}</li>
            <li>Exchange (USD): {formatUsd(exchangeUSDBalance)}</li>
            <li>Exchange (BTC): {formatBtc(exchangeBTCBalance)}</li>
            <li>Wallet (BTC): {formatBtc(walletBTCBalance)}</li>
          </ul>
        </div>

        {/* (B) Realized Gains */}
        <div className="card realized-gains-container">
          <h3>Realized Gains/Losses</h3>
          <p>Short Term: N/A</p>
          <p>Long Term: N/A</p>
          <p>
            Total Gains: {formatUsd(gainsAndLosses.total_gains)}
          </p>
          <p>
            Total Losses: {formatUsd(gainsAndLosses.total_losses)}
          </p>
        </div>

        {/* (C) Income / Interest / Rewards / Fees */}
        <div className="card income-fees-container">
          <h3>Income & Fees</h3>
          <p>Income (earned): {formatUsd(gainsAndLosses.income_earned)}</p>
          <p>Interest (earned): {formatUsd(gainsAndLosses.interest_earned)}</p>
          {/* If you have a “rewards” field eventually: 
              <p>Rewards: ...</p> 
          */}

          <br />
          <h4>Fees</h4>
          <p>Fees (USD): {formatUsd(gainsAndLosses.fees.USD)}</p>
          <p>Fees (BTC): {formatBtc(gainsAndLosses.fees.BTC)}</p>
          <p>Total Fees in USD (approx): {formatUsd(totalFeesUsd)}</p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
