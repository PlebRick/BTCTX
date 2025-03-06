import React, { useState, useEffect } from "react";
import api from "../api"; // Your centralized Axios/fetch wrapper
import "../styles/converter.css";

/**
 * BtcConverter:
 *  A component that allows conversion between USD, BTC, and Satoshi (sats).
 *  It has two modes:
 *    - Auto mode: automatically fetches the current BTC price periodically.
 *    - Manual mode: uses a manually-input price, which defaults to a freshly fetched value (or 0 if it fails).
 *
 * Key Points:
 *  1. We default to auto mode (isAutoPrice = true).
 *  2. When auto mode is active, we fetch the price on mount + poll every 2 minutes.
 *  3. Toggling from auto -> manual triggers a single fetch to set the manual price.
 *     If it fails, we default to 0. (The user can then edit this value freely.)
 *  4. If the user toggles back to auto, we clear the manual price from the UI’s perspective
 *     (but keep an internal state if we want). The displayed price will now be autoBtcPrice.
 *  5. The conversion logic automatically updates the other fields whenever one is changed.
 */

const BtcConverter: React.FC = () => {
  // -------------------------------------------------------------------
  // 1) State: Toggle for manual vs. auto price
  //    - isAutoPrice: whether we are in auto-fetch mode or manual mode
  // -------------------------------------------------------------------
  const [isAutoPrice, setIsAutoPrice] = useState<boolean>(true);

  // Manually entered price (used only if isAutoPrice === false)
  // We’ll initialize it to 0, because if the auto fetch fails,
  // we might want to have a 0-based fallback anyway.
  const [manualBtcPrice, setManualBtcPrice] = useState<number>(0);

  // Auto‐fetched live price (only used if isAutoPrice === true)
  // If null, we treat it as "loading..."
  const [autoBtcPrice, setAutoBtcPrice] = useState<number | null>(null);

  // -------------------------------------------------------------------
  // 2) Fields for USD, BTC, and sats
  //    These are the values shown in the form inputs.
  // -------------------------------------------------------------------
  const [usdValue, setUsdValue] = useState<string>("");
  const [btcValue, setBtcValue] = useState<string>("");
  const [satsValue, setSatsValue] = useState<string>("");

  // -------------------------------------------------------------------
  // 3) Auto mode: fetch the live BTC price periodically if isAutoPrice
  // -------------------------------------------------------------------
  useEffect(() => {
    // If we are not in auto mode, clear the auto price and do nothing else here.
    if (!isAutoPrice) {
      setAutoBtcPrice(null);
      return;
    }

    // Helper function to fetch the live price once
    const fetchLivePrice = () => {
      api
        .get<LiveBtcPriceResponse>("/bitcoin/price") // => GET /api/bitcoin/price
        .then((res) => {
          // Expect { USD: number }
          if (res.data && typeof res.data.USD === "number") {
            setAutoBtcPrice(res.data.USD);
          } else {
            // If the response doesn't have a USD field, set to 0 to fail gracefully
            setAutoBtcPrice(0);
          }
        })
        .catch((err) => {
          console.error("Failed to fetch live BTC price:", err);
          // Fall back to 0 if API call fails
          setAutoBtcPrice(0);
        });
    };

    // Initial fetch on mount or when user toggles to auto
    fetchLivePrice();

    // Poll every 2 minutes (120_000 ms). Adjust as you like.
    const intervalId = setInterval(fetchLivePrice, 120_000);

    // Cleanup interval on unmount or when toggling away from auto
    return () => clearInterval(intervalId);
  }, [isAutoPrice]);

  // -------------------------------------------------------------------
  // 4) Manual mode: whenever we toggle FROM auto -> manual, fetch once
  //    to get a current price to start with (or fall back to 0 if fail).
  //    That price is placed into manualBtcPrice, which the user can edit.
  // -------------------------------------------------------------------
  useEffect(() => {
    // If we are in auto mode, do nothing here.
    if (isAutoPrice) return;

    // If we just switched from auto to manual, fetch the current price once.
    const fetchManualPrice = async () => {
      try {
        const res = await api.get<LiveBtcPriceResponse>("/bitcoin/price");
        if (res.data && typeof res.data.USD === "number") {
          setManualBtcPrice(res.data.USD);
        } else {
          setManualBtcPrice(0);
        }
      } catch (err) {
        console.error("Failed to fetch manual BTC price:", err);
        setManualBtcPrice(0);
      }
    };

    // Execute the fetch once
    fetchManualPrice();
  }, [isAutoPrice]);

  // -------------------------------------------------------------------
  // 5) Decide which BTC price to use in conversions
  //    - If auto mode is on and auto price is not null, use autoBtcPrice.
  //    - Otherwise, use manualBtcPrice.
  //    NOTE: If autoBtcPrice is null, we’re likely still "Loading..."
  // -------------------------------------------------------------------
  const effectiveBtcPrice =
    isAutoPrice && autoBtcPrice !== null ? autoBtcPrice : manualBtcPrice;

  // -------------------------------------------------------------------
  // 6) A small helper for rounding to 5 decimal places
  // -------------------------------------------------------------------
  const round = (num: number) => Math.round(num * 100_000) / 100_000;

  // -------------------------------------------------------------------
  // 7) Conversion Logic:
  //    Whenever the user changes one of the three fields (USD, BTC, or sats),
  //    we recalculate the other two.
  // -------------------------------------------------------------------
  /**
   * handleUsdChange:
   *  - Called whenever the user types in the USD input box.
   *  - We parse that as a number, then compute the corresponding BTC and sats values.
   */
  const handleUsdChange = (value: string) => {
    setUsdValue(value);
    const usdNum = parseFloat(value) || 0;

    // 1 BTC = effectiveBtcPrice USD
    const btcNum = usdNum / effectiveBtcPrice;
    // 1 BTC = 100,000,000 sats
    const satsNum = btcNum * 100_000_000;

    setBtcValue(btcNum ? round(btcNum).toString() : "");
    setSatsValue(satsNum ? Math.floor(satsNum).toString() : "");
  };

  /**
   * handleBtcChange:
   *  - Called whenever the user types in the BTC input box.
   *  - We parse that as a number, then compute the corresponding USD and sats values.
   */
  const handleBtcChange = (value: string) => {
    setBtcValue(value);
    const btcNum = parseFloat(value) || 0;

    // USD = BTC * price
    const usdNum = btcNum * effectiveBtcPrice;
    // Sats = BTC * 100,000,000
    const satsNum = btcNum * 100_000_000;

    setUsdValue(usdNum ? round(usdNum).toString() : "");
    setSatsValue(satsNum ? Math.floor(satsNum).toString() : "");
  };

  /**
   * handleSatsChange:
   *  - Called whenever the user types in the Satoshi input box.
   *  - We parse that as a number, then compute the corresponding BTC and USD.
   */
  const handleSatsChange = (value: string) => {
    setSatsValue(value);
    const satsNum = parseFloat(value) || 0;

    // BTC = sats / 100,000,000
    const btcNum = satsNum / 100_000_000;
    // USD = BTC * price
    const usdNum = btcNum * effectiveBtcPrice;

    setBtcValue(btcNum ? round(btcNum).toString() : "");
    setUsdValue(usdNum ? round(usdNum).toString() : "");
  };

  // -------------------------------------------------------------------
  // 8) Render
  // -------------------------------------------------------------------
  return (
    <div className="converter">
      <div className="converter-title">Sats Converter</div>

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
            BTC Price:&nbsp;
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
