import React, { useState } from 'react';
import '../styles/converter.css'; // We'll create a matching CSS file

const BtcConverter: React.FC = () => {
  // Toggle for manual vs. auto
  const [isAutoPrice, setIsAutoPrice] = useState<boolean>(false);

  // The “live” or “manual” price of 1 BTC in USD
  // In real usage, you'd feed the `autoPrice` from an API if isAutoPrice is true
  const [manualBtcPrice, setManualBtcPrice] = useState<number>(23000); // Example default

  // Conversion input fields
  const [usdValue, setUsdValue] = useState<string>('');
  const [btcValue, setBtcValue] = useState<string>('');
  const [satsValue, setSatsValue] = useState<string>('');

  // Grab the "effective" BTC price - 
  // If `isAutoPrice` is true, you might pull from an external prop or context (live feed).
  // For now, we’ll do a placeholder autoPrice to illustrate.
  const autoPrice = 25000; // pretend this is your “live feed” fallback
  const effectiveBtcPrice = isAutoPrice ? autoPrice : manualBtcPrice;

  // Helper for rounding to a few decimals
  const round = (num: number) => {
    return Math.round(num * 100000) / 100000;
  };

  // Whenever one field changes, update the others:
  const handleUsdChange = (value: string) => {
    setUsdValue(value);
    const usdNum = parseFloat(value) || 0;

    // 1 BTC = effectiveBtcPrice USD
    const btcNum = usdNum / effectiveBtcPrice;
    // 1 BTC = 100,000,000 sats
    const satsNum = btcNum * 100000000;

    setBtcValue(btcNum ? round(btcNum).toString() : '');
    setSatsValue(satsNum ? Math.floor(satsNum).toString() : '');
  };

  const handleBtcChange = (value: string) => {
    setBtcValue(value);
    const btcNum = parseFloat(value) || 0;

    // convert BTC -> USD
    const usdNum = btcNum * effectiveBtcPrice;
    // convert BTC -> Satoshis
    const satsNum = btcNum * 100000000;

    setUsdValue(usdNum ? round(usdNum).toString() : '');
    setSatsValue(satsNum ? Math.floor(satsNum).toString() : '');
  };

  const handleSatsChange = (value: string) => {
    setSatsValue(value);
    const satsNum = parseFloat(value) || 0;

    // convert sats -> BTC
    const btcNum = satsNum / 100000000;
    // convert BTC -> USD
    const usdNum = btcNum * effectiveBtcPrice;

    setBtcValue(btcNum ? round(btcNum).toString() : '');
    setUsdValue(usdNum ? round(usdNum).toString() : '');
  };

  return (
    <div className="converter">
      <div className="converter-title">BTC Converter</div>

      {/* Toggle between manual vs auto mode */}
      <div className="price-toggle">
        <button
          className={!isAutoPrice ? 'toggle-btn active' : 'toggle-btn'}
          onClick={() => setIsAutoPrice(false)}
        >
          Manual Price
        </button>
        <button
          className={isAutoPrice ? 'toggle-btn active' : 'toggle-btn'}
          onClick={() => setIsAutoPrice(true)}
        >
          Auto Price
        </button>
      </div>

      {/* Manual Price Input (only show if not auto) */}
      {!isAutoPrice && (
        <div className="manual-price-row">
          <label htmlFor="manualPrice">BTC Price (USD)</label>
          <input
            id="manualPrice"
            type="number"
            value={manualBtcPrice}
            onChange={(e) => setManualBtcPrice(parseFloat(e.target.value) || 0)}
          />
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
