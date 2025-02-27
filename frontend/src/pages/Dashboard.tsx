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

// Import numeric helpers
import {
  parseDecimal,
  formatUsd,
  formatBtc,
} from "../utils/format";

const Dashboard: React.FC = () => {
  /**
   * State for account balances (AccountBalance[]). The local
   * definition of `AccountBalance` was removed. It is now
   * declared globally in global.d.ts.
   */
  const [balances, setBalances] = useState<AccountBalance[] | null>(null);

  // Individual balances for special accounts
  const [bankBalance, setBankBalance] = useState<number>(0);
  const [exchangeUSDBalance, setExchangeUSDBalance] = useState<number>(0);
  const [exchangeBTCBalance, setExchangeBTCBalance] = useState<number>(0);
  const [walletBTCBalance, setWalletBTCBalance] = useState<number>(0);

  // Totals for the portfolio summary
  const [totalBTC, setTotalBTC] = useState<number>(0);
  const [totalUSD, setTotalUSD] = useState<number>(0);

  /**
   * GainsAndLosses after parsing. GainsAndLosses + GainsAndLossesRaw
   * are now globally defined.
   */
  const [gainsAndLosses, setGainsAndLosses] = useState<GainsAndLosses | null>(null);

  // State for any fetch errors
  const [fetchError, setFetchError] = useState<string | null>(null);

  // -----------------------------
  // Fetch Account Balances
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
        // Store raw AccountBalance data
        setBalances(data as AccountBalance[]);
      })
      .catch((err) => {
        console.error("Error fetching balances:", err);
        setFetchError(String(err));
      });
  }, []);

  // Process the fetched balances to set special account balances & totals
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

      if (acc.name === "Bank" && acc.currency === "USD") {
        bank = numericBalance;
      } else if (acc.name === "Wallet" && acc.currency === "BTC") {
        walletBTC = numericBalance;
      } else if (acc.name === "Exchange USD" && acc.currency === "USD") {
        exchUSD = numericBalance;
      } else if (acc.name === "Exchange BTC" && acc.currency === "BTC") {
        exchBTC = numericBalance;
      }

      if (acc.currency === "BTC") {
        totalBtcTemp += numericBalance;
      } else if (acc.currency === "USD") {
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
  // Fetch Gains and Losses
  // -----------------------------
  useEffect(() => {
    api
      .get<GainsAndLossesRaw>("/calculations/gains-and-losses")
      .then((response) => {
        const raw = response.data;
        console.log("Fetched gains and losses data:", raw);

        // Manual parsing of GainsAndLossesRaw into GainsAndLosses
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

  // Placeholder data
  const unrealizedGains = 0;
  const portfolioChartPlaceholder = "(Chart Placeholder)";

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

  return (
    <div className="dashboard">
      {/* Top row: Portfolio and BTC Price */}
      <div className="dashboard-row top-row">
        <div className="card">
          <h5>Portfolio</h5>
          <p>BTC Balance: {formatBtc(totalBTC)}</p>
          <p>USD Value: {formatUsd(totalUSD)}</p>
          <p>Unrealized Gains/Losses: {unrealizedGains}</p>
          <p>Portfolio Chart: {portfolioChartPlaceholder}</p>
        </div>
        <div className="card">
          <h5>Bitcoin Price</h5>
          <p>Placeholder for live BTC price & chart</p>
        </div>
      </div>

      {/* Bottom row: Accounts */}
      <div className="dashboard-row bottom-row">
        <div className="card">
          <h5>Bank</h5>
          <p>USD Balance: {formatUsd(bankBalance)}</p>
        </div>
        <div className="card">
          <h5>Exchange</h5>
          <p>USD Balance: {formatUsd(exchangeUSDBalance)}</p>
          <p>BTC Balance: {formatBtc(exchangeBTCBalance)}</p>
        </div>
        <div className="card">
          <h5>Wallet</h5>
          <p>BTC Balance: {formatBtc(walletBTCBalance)}</p>
        </div>
      </div>

      {/* Gains and Losses row */}
      <div className="dashboard-row bottom-row">
        <div className="card">
          <h5>Realized Gains</h5>
          <p>Short term: N/A</p>
          <p>Long term: N/A</p>
          <p>Total: {formatUsd(gainsAndLosses.sells_proceeds)}</p>
        </div>
        <div className="card">
          <h5>Other Gains</h5>
          <p>Income: {formatUsd(gainsAndLosses.income_earned)}</p>
          <p>Interest: {formatUsd(gainsAndLosses.interest_earned)}</p>
          <p>Spent: {formatUsd(gainsAndLosses.withdrawals_spent)}</p>
        </div>
        <div className="card">
          <h5>Losses</h5>
          <p>Short term: N/A</p>
          <p>Long term: N/A</p>
          <p>Total: {formatUsd(gainsAndLosses.total_losses)}</p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
