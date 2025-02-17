/**
 * TransactionForm.tsx
 *
 * This component provides a dynamic form for creating transactions.
 * It preserves the current UI behavior:
 *   - The user selects a transaction type first.
 *   - When "Exchange" is selected, a currency selector appears.
 *   - Based on the selected currency (USD or BTC), the form auto-maps to the appropriate sub-account.
 *
 * Note: Ensure your tsconfig.json (or tsconfig.app.json) has:
 *   "target": "es2017",
 *   "lib": ["DOM", "DOM.Iterable", "ESNext", "ES2015"],
 *   "jsx": "react-jsx",
 *   "esModuleInterop": true
 * to resolve errors related to Promise, JSX, and Iterable.
 */

import React, { useEffect, useState } from "react";
import axios from "axios";
import "../styles/transactionForm.css";

// Interface for component props.
interface TransactionFormProps {
  id: string; // Used as the id attribute on the form element.
  onSubmitSuccess?: () => void; // Callback triggered upon successful submission.
}

// Define a type for account options in the UI.
type AccountOption = "Bank" | "Wallet" | "Exchange";

// Define a type for currency.
type Currency = "USD" | "BTC";

// Define a type for transaction types.
type TransactionType = "DEPOSIT" | "WITHDRAWAL" | "TRANSFER" | "BUY" | "SELL";

// Interface for our form data state.
interface TransactionFormData {
  type: TransactionType;
  // For deposit/withdrawal, the user selects a single account option.
  account?: AccountOption;
  // For the "Exchange" option, the currency selection determines the actual account used.
  currency?: Currency;
  // Numeric fields for amounts, price, fees, etc.
  amount?: number;
  price?: number; // Price per BTC (for buy/sell)
  proceeds_usd?: number; // Total USD involved (for buy/sell)
  fee_amount?: number;
  fee_currency?: Currency;
  external_ref?: string; // For external deposits/withdrawals
}

// The TransactionForm component now accepts props defined by TransactionFormProps.
const TransactionForm: React.FC<TransactionFormProps> = ({ id, onSubmitSuccess }) => {
  // Initialize form state; default type is "DEPOSIT" and default currency "USD".
  const [formData, setFormData] = useState<TransactionFormData>({
    type: "DEPOSIT",
    currency: "USD",
  });

  // Example useEffect to log when the component mounts.
  useEffect(() => {
    console.log("TransactionForm mounted");
  }, []);

  // Fixed options for account selection in the UI.
  // The user will see "Bank", "Wallet", and "Exchange".
  const accountOptions: AccountOption[] = ["Bank", "Wallet", "Exchange"];

  // Handler when the transaction type changes.
  const handleTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newType = e.target.value as TransactionType;
    setFormData({
      ...formData,
      type: newType,
      // Optionally reset other fields when type changes.
    });
  };

  // Handler for account selection.
  const handleAccountChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selected = e.target.value as AccountOption;
    setFormData({
      ...formData,
      account: selected,
    });
  };

  // Handler for currency selection; only shown when "Exchange" is selected.
  const handleCurrencyChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedCurrency = e.target.value as Currency;
    setFormData({
      ...formData,
      currency: selectedCurrency,
    });
  };

  // Handler for form submission.
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Fixed mapping for backend account IDs:
    // Bank -> 1, Wallet -> 2, ExchangeUSD -> 3, ExchangeBTC -> 4.
    const accountMapping: Record<string, number> = {
      Bank: 1,
      Wallet: 2,
      ExchangeUSD: 3,
      ExchangeBTC: 4,
    };

    // Determine the actual account ID to use.
    let selectedAccountId: number = 0;
    if (formData.account === "Exchange") {
      // Use the currency field to select the correct sub-account.
      selectedAccountId =
        formData.currency === "USD"
          ? accountMapping["ExchangeUSD"]
          : accountMapping["ExchangeBTC"];
    } else if (formData.account) {
      selectedAccountId = accountMapping[formData.account];
    }

    // Build the payload for the API.
    // For DEPOSIT, funds come into the selected account (to_account_id).
    // For WITHDRAWAL, funds leave the selected account (from_account_id).
    const payload = {
      type: formData.type,
      from_account_id:
        formData.type === "WITHDRAWAL" ? selectedAccountId : null,
      to_account_id: formData.type === "DEPOSIT" ? selectedAccountId : null,
      amount: formData.amount,
      proceeds_usd: formData.proceeds_usd,
      fee_amount: formData.fee_amount,
      fee_currency: formData.fee_currency,
      external_ref: formData.external_ref,
      timestamp: new Date().toISOString(),
    };

    try {
      await axios.post("http://127.0.0.1:8000/transactions/", payload);
      alert("Transaction submitted successfully!");
      if (onSubmitSuccess) {
        onSubmitSuccess();
      }
      // Optionally, reset form fields here.
    } catch {
      alert("Error submitting transaction.");
    }
  };

  return (
    <form id={id} className="transaction-form" onSubmit={handleSubmit}>
      <h2>New Transaction</h2>
      
      {/* Transaction Type Selector */}
      <div className="form-group">
        <label>Transaction Type</label>
        <select value={formData.type} onChange={handleTypeChange}>
          <option value="DEPOSIT">Deposit</option>
          <option value="WITHDRAWAL">Withdrawal</option>
          <option value="TRANSFER">Transfer</option>
          <option value="BUY">Buy (BTC for USD)</option>
          <option value="SELL">Sell (BTC for USD)</option>
        </select>
      </div>

      {/* Account selection for Deposit/Withdrawal */}
      {(formData.type === "DEPOSIT" ||
        formData.type === "WITHDRAWAL") && (
        <div className="form-group">
          <label>Account</label>
          <select value={formData.account || ""} onChange={handleAccountChange}>
            <option value="">Select Account</option>
            {accountOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* If "Exchange" is selected, display currency selector */}
      {formData.account === "Exchange" && (
        <div className="form-group">
          <label>Currency</label>
          <select value={formData.currency} onChange={handleCurrencyChange}>
            <option value="USD">USD</option>
            <option value="BTC">BTC</option>
          </select>
        </div>
      )}

      {/* Amount input */}
      <div className="form-group">
        <label>
          Amount {formData.currency ? `(${formData.currency})` : ""}
        </label>
        <input
          type="number"
          step={formData.currency === "USD" ? "0.01" : "0.00000001"}
          value={formData.amount || ""}
          onChange={(e) =>
            setFormData({
              ...formData,
              amount: parseFloat(e.target.value) || 0,
            })
          }
        />
      </div>

      {/* Additional fields for BUY/SELL transactions */}
      {(formData.type === "BUY" || formData.type === "SELL") && (
        <>
          <div className="form-group">
            <label>Price (USD per BTC)</label>
            <input
              type="number"
              step="0.01"
              value={formData.price || ""}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  price: parseFloat(e.target.value) || 0,
                })
              }
            />
          </div>
          <div className="form-group">
            <label>Total USD</label>
            <input
              type="number"
              step="0.01"
              value={formData.proceeds_usd || ""}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  proceeds_usd: parseFloat(e.target.value) || 0,
                })
              }
            />
          </div>
        </>
      )}

      {/* Fee input */}
      <div className="form-group">
        <label>Fee (optional)</label>
        <input
          type="number"
          step="0.01"
          value={formData.fee_amount || ""}
          onChange={(e) =>
            setFormData({
              ...formData,
              fee_amount: parseFloat(e.target.value) || 0,
            })
          }
        />
        <select
          value={formData.fee_currency || ""}
          onChange={(e) =>
            setFormData({
              ...formData,
              fee_currency: e.target.value as Currency,
            })
          }
        >
          <option value="">Select Fee Currency</option>
          <option value="USD">USD</option>
          <option value="BTC">BTC</option>
        </select>
      </div>

      {/* External Reference for Deposits/Withdrawals */}
      {(formData.type === "DEPOSIT" || formData.type === "WITHDRAWAL") && (
        <div className="form-group">
          <label>External Reference</label>
          <input
            type="text"
            placeholder="e.g., Coinbase, Personal Wallet"
            value={formData.external_ref || ""}
            onChange={(e) =>
              setFormData({
                ...formData,
                external_ref: e.target.value,
              })
            }
          />
        </div>
      )}

      <button type="submit">Submit Transaction</button>
    </form>
  );
};

export default TransactionForm;
