/**
 * Dashboard.tsx
 *
 * Shows aggregated balances & gains/losses. Uses globally defined types:
 * - AccountBalance
 * - GainsAndLosses
 * - GainsAndLossesRaw
 * for typed state management and fetch handling.
 */

import React, { useEffect, useState } from "react";
import api from "../api"; // Centralized API client
import "../styles/dashboard.css";

// Numeric helpers
import {
  parseDecimal,
  formatUsd,
  formatBtc,
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

  // Example placeholders
  const [fetchError, setFetchError] = useState<string | null>(null);
  const unrealizedGains = 0; // If not provided by backend, keep as 0 or placeholder

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

  // Process fetched balances into local state
  useEffect(() => {
    if (!balances) return;

    let bank = 0;
    let exchUSD = 0;
    let exchBTC = 0;
    let walletBTC = 0;

    let totalBtcTemp = 0;
    let totalUsdTemp = 0;

    balances.forEach((acc) => {
      const numericBalance = parseDecimal(acc.balance);
      if (Number.isNaN(numericBalance)) {
        console.warn("Encountered NaN balance for account:", acc);
        return;
      }

      // Identify your known accounts by name/currency
      if (acc.name === "Bank" && acc.currency === "USD") {
        bank = numericBalance;
      } else if (acc.name === "Wallet" && acc.currency === "BTC") {
        walletBTC = numericBalance;
      } else if (acc.name === "Exchange USD" && acc.currency === "USD") {
        exchUSD = numericBalance;
      } else if (acc.name === "Exchange BTC" && acc.currency === "BTC") {
        exchBTC = numericBalance;
      }

      // Tally total BTC / USD across all accounts
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
        const raw = response.data;
        console.log("Fetched gains and losses data:", raw);

        // Convert GainsAndLossesRaw -> GainsAndLosses (numeric)
        const parsed: GainsAndLosses = {
          sells_proceeds: parseDecimal(raw.sells_proceeds),
          withdrawals_spent: parseDecimal(raw.withdrawals_spent),
          income_earned: parseDecimal(raw.income_earned),
          interest_earned: parseDecimal(raw.interest_earned),
          fees: {
            USD: parseDecimal(raw.fees.USD),
            BTC: parseDecimal(raw.fees.BTC),
          },
          total_gains: parseDecimal(raw.total_gains),
          total_losses: parseDecimal(raw.total_losses),
        };

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
          {/* Sells Proceeds is how much total USD you got from selling BTC. */}
          <p>Proceeds from Sells: {formatUsd(gainsAndLosses.sells_proceeds)}</p>
          <p>Income: {formatUsd(gainsAndLosses.income_earned)}</p>
          <p>Interest: {formatUsd(gainsAndLosses.interest_earned)}</p>
          {/* This is total USD spent via “Withdrawal” transactions. */}
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
