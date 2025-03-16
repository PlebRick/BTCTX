//frontend/src/pages/Dashboard.tsx
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
  // ------------------ 1) STATE DECLARATIONS ------------------
  const [balances, setBalances] = useState<AccountBalance[] | null>(null);
  const [bankBalance, setBankBalance] = useState<number>(0);
  const [exchangeUSDBalance, setExchangeUSDBalance] = useState<number>(0);
  const [exchangeBTCBalance, setExchangeBTCBalance] = useState<number>(0);
  const [walletBTCBalance, setWalletBTCBalance] = useState<number>(0);
  const [totalBTC, setTotalBTC] = useState<number>(0);
  const [totalUSD, setTotalUSD] = useState<number>(0);

  // Cost basis & Gains
  const [averageBtcCostBasis, setAverageBtcCostBasis] = useState<number | null>(null);
  const [gainsAndLosses, setGainsAndLosses] = useState<GainsAndLosses | null>(null);

  // BTC Price & error states
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [currentBtcPrice, setCurrentBtcPrice] = useState<number | null>(null);
  const [isPriceLoading, setIsPriceLoading] = useState(true);

  // ------------------ 2) FETCH LIVE BTC PRICE ------------------
  useEffect(() => {
    setIsPriceLoading(true);
    api
      .get("/bitcoin/price") // => GET /api/bitcoin/price
      .then((res) => {
        if (res.data && res.data.USD) {
          setCurrentBtcPrice(res.data.USD);
        }
      })
      .catch((err) => {
        console.error("Error fetching live BTC price:", err);
      })
      .finally(() => {
        setIsPriceLoading(false);
      });
  }, []);

  // ------------------ 3) FETCH AVERAGE COST BASIS ------------------
  useEffect(() => {
    api
      .get<AverageCostBasis>("/calculations/average-cost-basis")
      .then((res) => {
        setAverageBtcCostBasis(res.data.averageCostBasis);
      })
      .catch((err) => {
        console.error("Error fetching average cost basis:", err);
      });
  }, []);

  // ------------------ 4) FETCH ACCOUNT BALANCES ------------------
  useEffect(() => {
    api
      .get("/calculations/accounts/balances")
      .then((response) => {
        const data = response.data;
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

  // ------------------ 5) CALCULATE TOTALS ------------------
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

    setBankBalance(bank);
    setExchangeUSDBalance(exchUSD);
    setExchangeBTCBalance(exchBTC);
    setWalletBTCBalance(wBTC);
    setTotalBTC(totalBtcTemp);
    setTotalUSD(totalUsdTemp);
  }, [balances]);

  // ------------------ 6) FETCH GAINS & LOSSES ------------------
  useEffect(() => {
    api
      .get<GainsAndLossesRaw>("/calculations/gains-and-losses")
      .then((response) => {
        const parsed = parseGainsAndLosses(response.data);
        setGainsAndLosses(parsed);
      })
      .catch((err) => {
        console.error("Error fetching gains & losses:", err);
        setFetchError(String(err));
      });
  }, []);

  // ------------------ 7) ERROR / LOADING HANDLING ------------------
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

  // ------------------ 8) RENDER DASHBOARD ------------------
  return (
    <div className="dashboard">
      {/* =================== Top Row =================== */}
      <div className="top-row">
        {/* Portfolio Overview Card */}
        <div className="card portfolio-overview">
          <h3>Portfolio Overview</h3>

          {/* 1) BTC Balance */}
          <p>BTC Balance: {formatBtc(totalBTC)}</p>

          {/* 2) BTC Cost Basis (new line just below BTC Balance) */}
          <p>
            BTC Cost Basis:{" "}
            {averageBtcCostBasis !== null
              ? formatUsd(averageBtcCostBasis)
              : "Loading..."}
          </p>

          {/* 3) USD Balance */}
          <p>USD Balance: {formatUsd(totalUSD)}</p>

          {/* 4) Unrealized Gains/Losses */}
          {isPriceLoading || currentBtcPrice === null || averageBtcCostBasis === null ? (
            <p>Unrealized Gains/Losses: Loading...</p>
          ) : (
            <p>
              Unrealized Gains/Losses:{" "}
              {(() => {
                const gains = (currentBtcPrice - averageBtcCostBasis) * totalBTC;
                const isGain = gains >= 0;
                const signSymbol = isGain ? "+" : "-";
                const displayAmount = Math.abs(gains);
                return (
                  <span style={{ color: isGain ? "green" : "red" }}>
                    {signSymbol}
                    {formatUsd(displayAmount)}
                  </span>
                );
              })()}
            </p>
          )}

          {/* Placeholder for portfolio chart */}
          <div className="portfolio-chart-placeholder">
            <p>Portfolio Holdings Chart (Placeholder)</p>
          </div>
        </div>

        {/* Bitcoin Price Card */}
        <div className="card btc-price-container">
          <h3>Bitcoin Price</h3>
          <p>
            Current BTC Price:{" "}
            {isPriceLoading ? (
              "Loading..."
            ) : currentBtcPrice !== null ? (
              <strong>
                $
                {currentBtcPrice.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </strong>
            ) : (
              "Error fetching price"
            )}
          </p>
          <div className="btc-price-chart-placeholder">
            <p>Live BTC Price Chart (Placeholder)</p>
          </div>
        </div>
      </div>

      {/* =================== Bottom Row =================== */}
      <div className="bottom-row">
        {/* Account Balances Card */}
        <div className="card account-balances-container">
          <h3>Account Balances</h3>
          <ul>
            <li>Bank (USD): {formatUsd(bankBalance)}</li>
            <li>Exchange (USD): {formatUsd(exchangeUSDBalance)}</li>
            <li>Exchange (BTC): {formatBtc(exchangeBTCBalance)}</li>
            <li>Wallet (BTC): {formatBtc(walletBTCBalance)}</li>
          </ul>
        </div>

        {/* Realized Gains/Losses Card */}
        <div className="card realized-gains-container">
          <h3>Realized Gains/Losses (FIFO)</h3>
          <p>
            <strong>Short‐Term Gains:</strong>{" "}
            <span style={{ color: gainsAndLosses.short_term_gains > 0 ? "green" : "white" }}>
              {formatUsd(gainsAndLosses.short_term_gains)}
            </span>
          </p>
          <p>
            <strong>Short‐Term Losses:</strong>{" "}
            <span style={{ color: gainsAndLosses.short_term_losses > 0 ? "red" : "white" }}>
              {formatUsd(gainsAndLosses.short_term_losses)}
            </span>
          </p>
          <p>
            <strong>Net Short‐Term:</strong>{" "}
            <span
              style={{
                color:
                  gainsAndLosses.short_term_net > 0
                    ? "green"
                    : gainsAndLosses.short_term_net < 0
                    ? "red"
                    : "white",
              }}
            >
              {formatUsd(gainsAndLosses.short_term_net)}
            </span>
          </p>
          <hr />
          <p>
            <strong>Long‐Term Gains:</strong>{" "}
            <span style={{ color: gainsAndLosses.long_term_gains > 0 ? "green" : "white" }}>
              {formatUsd(gainsAndLosses.long_term_gains)}
            </span>
          </p>
          <p>
            <strong>Long‐Term Losses:</strong>{" "}
            <span style={{ color: gainsAndLosses.long_term_losses > 0 ? "red" : "white" }}>
              {formatUsd(gainsAndLosses.long_term_losses)}
            </span>
          </p>
          <p>
            <strong>Net Long‐Term:</strong>{" "}
            <span
              style={{
                color:
                  gainsAndLosses.long_term_net > 0
                    ? "green"
                    : gainsAndLosses.long_term_net < 0
                    ? "red"
                    : "white",
              }}
            >
              {formatUsd(gainsAndLosses.long_term_net)}
            </span>
          </p>
          <hr />
          <p>
            <strong>Total Net Capital Gains:</strong>{" "}
            <span
              style={{
                color:
                  gainsAndLosses.total_net_capital_gains > 0
                    ? "green"
                    : gainsAndLosses.total_net_capital_gains < 0
                    ? "red"
                    : "white",
              }}
            >
              {formatUsd(gainsAndLosses.total_net_capital_gains)}
            </span>
          </p>
        </div>

        {/* Income & Fees Card */}
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
          <p>
            Total Income (Income+Interest+Rewards):{" "}
            {formatUsd(gainsAndLosses.total_income)}
          </p>
          <br />
          <h4>Fees</h4>
          <p>Fees (USD): {formatUsd(gainsAndLosses.fees.USD)}</p>
          <p>Fees (BTC): {formatBtc(gainsAndLosses.fees.BTC)}</p>
          {isPriceLoading ? (
            <p>Total Fees in USD: Loading...</p>
          ) : currentBtcPrice !== null ? (
            <p>
              Total Fees in USD (approx):{" "}
              {formatUsd(
                gainsAndLosses.fees.USD + gainsAndLosses.fees.BTC * currentBtcPrice
              )}
            </p>
          ) : (
            <p>Total Fees in USD: N/A</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
