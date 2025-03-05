/**
 * Dashboard.tsx
 *
 * Displays portfolio overview, balances, realized gains, etc.
 * Now also shows a live BTC price (replacing the placeholder).
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
  // 1) State for Account Balances
  // -----------------------------
  const [balances, setBalances] = useState<AccountBalance[] | null>(null);
  const [bankBalance, setBankBalance] = useState<number>(0);
  const [exchangeUSDBalance, setExchangeUSDBalance] = useState<number>(0);
  const [exchangeBTCBalance, setExchangeBTCBalance] = useState<number>(0);
  const [walletBTCBalance, setWalletBTCBalance] = useState<number>(0);
  const [totalBTC, setTotalBTC] = useState<number>(0);
  const [totalUSD, setTotalUSD] = useState<number>(0);

  // -----------------------------
  // 2) Gains & Losses
  // -----------------------------
  const [gainsAndLosses, setGainsAndLosses] = useState<GainsAndLosses | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Placeholder for now (will incorporate BTC price for unrealized gains later)
  const unrealizedGains = 0;

  // Example BTC price used for fee calculations or placeholders:
  // (You can remove this if you prefer to use the actual live price for fees.)
  const BTC_PRICE = 25000;

  // -----------------------------
  // 3) Fetch live BTC price
  //    (Replacing the placeholder text in upper-right card)
  // -----------------------------
  const [currentBtcPrice, setCurrentBtcPrice] = useState<number | null>(null);

  useEffect(() => {
    api
      .get("/bitcoin/price") // => GET /api/bitcoin/price
      .then((res) => {
        // Should get { "USD": <some number> }
        if (res.data && res.data.USD) {
          setCurrentBtcPrice(res.data.USD);
        }
      })
      .catch((err) => {
        console.error("Error fetching live BTC price:", err);
        // Could handle errors or set a fallback price if desired
      });
  }, []);

  // -----------------------------
  // 4) Fetch account balances
  // -----------------------------
  useEffect(() => {
    api
      .get("/calculations/accounts/balances")
      .then((response) => {
        const data = response.data;
        console.log("Fetched balances data:", data);

        if (!Array.isArray(data)) {
          throw new Error("Data is not an array. Received: " + JSON.stringify(data));
        }
        setBalances(data as AccountBalance[]);
      })
      .catch((err) => {
        console.error("Error fetching balances:", err);
        setFetchError(String(err));
      });
  }, []);

  // After balances arrive, compute totals
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

      // Tally totals
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

  // -----------------------------
  // 5) Fetch Gains and Losses
  // -----------------------------
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

  // -----------------------------
  // Basic error/loading states
  // -----------------------------
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
  const totalFeesUsd = gainsAndLosses.fees.USD + gainsAndLosses.fees.BTC * BTC_PRICE;

  // -----------------------------
  // 6) Render
  // -----------------------------
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

          {/* Placeholder for portfolio chart */}
          <div className="portfolio-chart-placeholder">
            <p>Portfolio Holdings Chart (Placeholder)</p>
          </div>
        </div>

        {/* Right: "Bitcoin Price" card */}
        <div className="card btc-price-container">
          <h3>Bitcoin Price</h3>
          <p>
            Current BTC Price:{" "}
            {currentBtcPrice !== null ? (
              <strong>
                $
                {currentBtcPrice.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </strong>
            ) : (
              "Loading..."
            )}
          </p>

          {/* Placeholder for a live BTC price chart (not implemented yet) */}
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

        {/* (B) Realized Gains: short- vs. long-term */}
        <div className="card realized-gains-container">
          <h3>Realized Gains/Losses</h3>
          <p>
            <strong>Short‐Term Gains:</strong>{" "}
            {formatUsd(gainsAndLosses.short_term_gains)}
          </p>
          <p>
            <strong>Short‐Term Losses:</strong>{" "}
            {formatUsd(gainsAndLosses.short_term_losses)}
          </p>
          <p>
            <strong>Net Short‐Term:</strong>{" "}
            {formatUsd(gainsAndLosses.short_term_net)}
          </p>
          <hr />
          <p>
            <strong>Long‐Term Gains:</strong>{" "}
            {formatUsd(gainsAndLosses.long_term_gains)}
          </p>
          <p>
            <strong>Long‐Term Losses:</strong>{" "}
            {formatUsd(gainsAndLosses.long_term_losses)}
          </p>
          <p>
            <strong>Net Long‐Term:</strong>{" "}
            {formatUsd(gainsAndLosses.long_term_net)}
          </p>
          <hr />
          <p>
            <strong>Total Net Capital Gains:</strong>{" "}
            {formatUsd(gainsAndLosses.total_net_capital_gains)}
          </p>
        </div>

        {/* (C) Income / Interest / Rewards / Fees */}
        <div className="card income-fees-container">
          <h3>Income & Fees</h3>
          <p>
            Income (earned): {formatUsd(gainsAndLosses.income_earned)}{" "}
            (<em>{formatBtc(gainsAndLosses.income_btc)}</em>)
          </p>
          <p>
            Interest (earned): {formatUsd(gainsAndLosses.interest_earned)}{" "}
            (<em>{formatBtc(gainsAndLosses.interest_btc)}</em>)
          </p>
          <p>
            Rewards (earned): {formatUsd(gainsAndLosses.rewards_earned)}{" "}
            (<em>{formatBtc(gainsAndLosses.rewards_btc)}</em>)
          </p>
          <p>
            Gifts (received): {formatUsd(gainsAndLosses.gifts_received)}{" "}
            (<em>{formatBtc(gainsAndLosses.gifts_btc)}</em>){" "}
            <span style={{ fontStyle: "italic" }}>
              (not added to income or gains)
            </span>
          </p>
          <p>Total Income (Income+Interest+Rewards): {formatUsd(gainsAndLosses.total_income)}</p>

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
