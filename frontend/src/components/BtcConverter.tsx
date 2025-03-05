import React, { useState, useEffect } from "react";
import api from "../api"; // centralized Axios or fetch wrapper
import "../styles/converter.css";

const BtcConverter: React.FC = () => {
  // Toggle for manual vs. auto
  const [isAutoPrice, setIsAutoPrice] = useState<boolean>(false);

  // Store the user-entered manual price
  const [manualBtcPrice, setManualBtcPrice] = useState<number>(23000); // Example default

  // This will hold the live price fetched from /bitcoin/price
  const [autoBtcPrice, setAutoBtcPrice] = useState<number | null>(null);

  // For user input values
  const [usdValue, setUsdValue] = useState<string>("");
  const [btcValue, setBtcValue] = useState<string>("");
  const [satsValue, setSatsValue] = useState<string>("");

  // Periodically fetch the live BTC price if in auto mode
  useEffect(() => {
    if (!isAutoPrice) {
      // Clear autoBtcPrice when leaving auto mode
      setAutoBtcPrice(null);
      return;
    }

    // Helper to fetch the live price
    const fetchLivePrice = () => {
      api
        .get("/bitcoin/price")
        .then((res) => {
          // Expect { "USD": 12345.67 }
          if (res.data && res.data.USD) {
            setAutoBtcPrice(res.data.USD);
          }
        })
        .catch((err) => {
          console.error("Failed to fetch live BTC price:", err);
        });
    };

    // 1) Fetch immediately on mode switch
    fetchLivePrice();

    // 2) Optionally poll every 30 seconds
    const intervalId = setInterval(fetchLivePrice, 30000);

    // Cleanup the interval on unmount or when switching away from auto
    return () => {
      clearInterval(intervalId);
    };
  }, [isAutoPrice]);

  // Decide which BTC price to use
  // If isAutoPrice == true, we use autoBtcPrice; if that’s null (still loading),
  // we fallback to manualBtcPrice to avoid NaN or 0 conversions.
  const effectiveBtcPrice =
    isAutoPrice && autoBtcPrice != null ? autoBtcPrice : manualBtcPrice;

  // Helper for rounding
  const round = (num: number) => Math.round(num * 100000) / 100000;

  // Whenever one field changes, recalc the others:
  const handleUsdChange = (value: string) => {
    setUsdValue(value);
    const usdNum = parseFloat(value) || 0;

    // 1 BTC = effectiveBtcPrice USD
    const btcNum = usdNum / effectiveBtcPrice;
    // 1 BTC = 100,000,000 sats
    const satsNum = btcNum * 100000000;

    setBtcValue(btcNum ? round(btcNum).toString() : "");
    setSatsValue(satsNum ? Math.floor(satsNum).toString() : "");
  };

  const handleBtcChange = (value: string) => {
    setBtcValue(value);
    const btcNum = parseFloat(value) || 0;

    const usdNum = btcNum * effectiveBtcPrice;
    const satsNum = btcNum * 100000000;

    setUsdValue(usdNum ? round(usdNum).toString() : "");
    setSatsValue(satsNum ? Math.floor(satsNum).toString() : "");
  };

  const handleSatsChange = (value: string) => {
    setSatsValue(value);
    const satsNum = parseFloat(value) || 0;

    const btcNum = satsNum / 100000000;
    const usdNum = btcNum * effectiveBtcPrice;

    setBtcValue(btcNum ? round(btcNum).toString() : "");
    setUsdValue(usdNum ? round(usdNum).toString() : "");
  };

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

      {/* Manual Price Input (only show if not in auto mode) */}
      {!isAutoPrice && (
        <div className="manual-price-row">
          <label htmlFor="manualPrice">BTC Price (USD)</label>
          <input
            id="manualPrice"
            type="number"
            value={manualBtcPrice}
            onChange={(e) =>
              setManualBtcPrice(parseFloat(e.target.value) || 0)
            }
          />
        </div>
      )}

      {/* If auto mode is active and we have an autoBtcPrice, show it */}
      {isAutoPrice && (
        <div className="auto-price-row">
          <p>
            Live BTC Price:{" "}
            {autoBtcPrice
              ? `$${autoBtcPrice.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}`
              : "Loading..."}
          </p>
        </div>
      )}

      {/* Conversion fields */}
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
