import React, { useState, useEffect } from "react";
import api from "../api"; // Your centralized Axios/fetch wrapper
import "../styles/converter.css";

const BtcConverter: React.FC = () => {
  // --------------------------------------------
  // 1) State: Toggle for manual vs. auto price
  // --------------------------------------------
  const [isAutoPrice, setIsAutoPrice] = useState<boolean>(false);

  // Manually entered price (only used if isAutoPrice == false)
  const [manualBtcPrice, setManualBtcPrice] = useState<number>(23000);

  // Auto‐fetched live price (only used if isAutoPrice == true)
  const [autoBtcPrice, setAutoBtcPrice] = useState<number | null>(null);

  // --------------------------------------------
  // 2) Fields for USD, BTC, and sats
  // --------------------------------------------
  const [usdValue, setUsdValue] = useState<string>("");
  const [btcValue, setBtcValue] = useState<string>("");
  const [satsValue, setSatsValue] = useState<string>("");

  // --------------------------------------------
  // 3) Auto mode: fetch the live BTC price
  //    periodically if isAutoPrice == true
  // --------------------------------------------
  useEffect(() => {
    if (!isAutoPrice) {
      // When switching back to manual mode, clear auto price
      setAutoBtcPrice(null);
      return;
    }

    // Helper to fetch the live price once
    const fetchLivePrice = () => {
      api
        .get("/bitcoin/price") // => GET /api/bitcoin/price
        .then((res) => {
          // Expect { USD: <number> }
          if (res.data && res.data.USD) {
            setAutoBtcPrice(res.data.USD);
          }
        })
        .catch((err) => {
          console.error("Failed to fetch live BTC price:", err);
        });
    };

    // Initial fetch on mount or when user toggles to auto
    fetchLivePrice();

    // Optionally poll every 30 seconds
    const intervalId = setInterval(fetchLivePrice, 30_000);

    // Cleanup interval on unmount or when toggling away from auto
    return () => clearInterval(intervalId);
  }, [isAutoPrice]);

  // --------------------------------------------
  // 4) Decide which BTC price to use
  //    - If auto mode is on, use autoBtcPrice (if available)
  //    - Otherwise use the manualBtcPrice
  // --------------------------------------------
  const effectiveBtcPrice =
    isAutoPrice && autoBtcPrice !== null ? autoBtcPrice : manualBtcPrice;

  // A small helper for rounding to 5 decimal places
  const round = (num: number) => Math.round(num * 100000) / 100000;

  // --------------------------------------------
  // 5) Conversion Logic
  //    Whenever user changes one field, recalc others
  // --------------------------------------------
  const handleUsdChange = (value: string) => {
    setUsdValue(value);
    const usdNum = parseFloat(value) || 0;

    // 1 BTC = effectiveBtcPrice USD
    const btcNum = usdNum / effectiveBtcPrice;
    const satsNum = btcNum * 100_000_000; // 1 BTC = 100,000,000 sats

    setBtcValue(btcNum ? round(btcNum).toString() : "");
    setSatsValue(satsNum ? Math.floor(satsNum).toString() : "");
  };

  const handleBtcChange = (value: string) => {
    setBtcValue(value);
    const btcNum = parseFloat(value) || 0;

    const usdNum = btcNum * effectiveBtcPrice;
    const satsNum = btcNum * 100_000_000;

    setUsdValue(usdNum ? round(usdNum).toString() : "");
    setSatsValue(satsNum ? Math.floor(satsNum).toString() : "");
  };

  const handleSatsChange = (value: string) => {
    setSatsValue(value);
    const satsNum = parseFloat(value) || 0;

    const btcNum = satsNum / 100_000_000;
    const usdNum = btcNum * effectiveBtcPrice;

    setBtcValue(btcNum ? round(btcNum).toString() : "");
    setUsdValue(usdNum ? round(usdNum).toString() : "");
  };

  // --------------------------------------------
  // 6) Render
  // --------------------------------------------
  return (
    <div className="converter">
      <div className="converter-title">sats converter</div>

      {/* Toggle between manual vs auto mode */}
      <div className="price-toggle">
        <button
          className={!isAutoPrice ? "toggle-btn active" : "toggle-btn"}
          onClick={() => setIsAutoPrice(false)}
        >
          Manual
        </button>
        <button
          className={isAutoPrice ? "toggle-btn active" : "toggle-btn"}
          onClick={() => setIsAutoPrice(true)}
        >
          Auto
        </button>
      </div>

      {/* Manual Price Input (only show if NOT in auto mode) */}
      {!isAutoPrice && (
        <div className="manual-price-row">
          <label htmlFor="manualPrice">BTC Price (USD)</label>
          <input
            id="manualPrice"
            type="number"
            value={manualBtcPrice}
            onChange={(e) => {
              const val = parseFloat(e.target.value);
              setManualBtcPrice(isNaN(val) ? 0 : val);
            }}
          />
        </div>
      )}

      {/* If auto mode is active, show the auto price (or "Loading...") */}
      {isAutoPrice && (
        <div className="auto-price-row">
          <p>
            Live BTC Price:&nbsp;
            {autoBtcPrice !== null
              ? `$${autoBtcPrice.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}`
              : "Loading..."}
          </p>
        </div>
      )}

      {/* Conversion fields: USD, BTC, Sats */}
      <div className="converter-row">
        <label htmlFor="usdInput">USD</label>
        <input
          id="usdInput"
          type="number"
          value={usdValue}
          onChange={(e) => handleUsdChange(e.target.value)}
        />
      </div>

      <div className="converter-row">
        <label htmlFor="btcInput">BTC</label>
        <input
          id="btcInput"
          type="number"
          value={btcValue}
          onChange={(e) => handleBtcChange(e.target.value)}
        />
      </div>

      <div className="converter-row">
        <label htmlFor="satsInput">Satoshi</label>
        <input
          id="satsInput"
          type="number"
          value={satsValue}
          onChange={(e) => handleSatsChange(e.target.value)}
        />
      </div>
    </div>
  );
};

export default BtcConverter;
