// frontend/src/components/TransactionForm.tsx

import React, { useState, useEffect } from "react";
import { useForm, SubmitHandler } from "react-hook-form";

// --- Define Types for Our Form Fields ---
type TransactionType = "deposit" | "withdrawal" | "transfer" | "buy" | "sell";
type AccountType = "bank" | "wallet" | "exchange";
type Currency = "USD" | "BTC";
type DepositSource = "N/A" | "My BTC" | "Gift" | "Income" | "Interest" | "Reward";
type WithdrawalPurpose = "N/A" | "Spent" | "Gift" | "Donation" | "Lost";

// --- Interface for the Form Data ---
interface TransactionFormData {
  dateTime: string;
  transactionType: TransactionType;
  // For Deposit/Withdrawal
  account?: AccountType;
  currency?: Currency;
  amount?: number;
  fee?: number;
  feeCurrency?: Currency;
  source?: DepositSource; // for deposits
  purpose?: WithdrawalPurpose; // for withdrawals
  // For Transfer
  fromAccount?: AccountType;
  fromCurrency?: Currency;
  amountFrom?: number;
  toAccount?: AccountType;
  toCurrency?: Currency;
  amountTo?: number;
  // For Buy/Sell
  amountUSD?: number;
  amountBTC?: number;
  tradeType?: "buy" | "sell"; // applicable for Sell form toggle
}

const TransactionForm: React.FC = () => {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<TransactionFormData>({
    defaultValues: {
      dateTime: new Date().toISOString().slice(0, 16), // format: YYYY-MM-DDTHH:MM
    },
  });

  // State to store the selected transaction type
  const [currentType, setCurrentType] = useState<TransactionType | "">("");
  
  // Watch for changes in account selections for dynamic behavior
  const account = watch("account");
  const fromAccount = watch("fromAccount");
  const toAccount = watch("toAccount");

  // For deposit/withdrawal: Auto-set the currency based on account type
  useEffect(() => {
    if (currentType === "deposit" || currentType === "withdrawal") {
      if (account === "bank") {
        setValue("currency", "USD");
      } else if (account === "wallet") {
        setValue("currency", "BTC");
      }
    }
  }, [account, currentType, setValue]);

  // For transfer: Auto-set fromCurrency and toCurrency based on account selections
  useEffect(() => {
    if (currentType === "transfer") {
      if (fromAccount === "bank") {
        setValue("fromCurrency", "USD");
      } else if (fromAccount === "wallet") {
        setValue("fromCurrency", "BTC");
      }
      if (toAccount === "bank") {
        setValue("toCurrency", "USD");
      } else if (toAccount === "wallet") {
        setValue("toCurrency", "BTC");
      }
    }
  }, [fromAccount, toAccount, currentType, setValue]);

  // When the transaction type changes, reset the form fields (while preserving the date/time)
  const onTransactionTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedType = e.target.value as TransactionType;
    setCurrentType(selectedType);
    reset({ transactionType: selectedType, dateTime: new Date().toISOString().slice(0, 16) });
  };

  // onSubmit handler to send data to your backend
  const onSubmit: SubmitHandler<TransactionFormData> = (data) => {
    console.log("Submitting transaction data:", data);
    // TODO: Replace this console.log with a fetch/axios call to your FastAPI endpoint
  };

  const fromCurrency = watch("fromCurrency");

  // Render dynamic fields based on the selected transaction type
  const renderDynamicFields = () => {
    switch (currentType) {
      case "deposit":
        return (
          <div>
            {/* Account Selection */}
            <div>
              <label>Account:</label>
              <select {...register("account", { required: "Account is required" })}>
                <option value="">Select Account</option>
                <option value="bank">Bank</option>
                <option value="wallet">Wallet</option>
                <option value="exchange">Exchange</option>
              </select>
              {errors.account && <span>{errors.account.message}</span>}
            </div>
            {/* Currency: Auto-set for bank and wallet; selectable for exchange */}
            <div>
              <label>Currency:</label>
              {account === "exchange" ? (
                <select {...register("currency", { required: "Currency is required" })}>
                  <option value="">Select Currency</option>
                  <option value="USD">USD</option>
                  <option value="BTC">BTC</option>
                </select>
              ) : (
                <input type="text" {...register("currency")} readOnly />
              )}
              {errors.currency && <span>{errors.currency.message}</span>}
            </div>
            {/* Amount Field */}
            <div>
              <label>Amount:</label>
              <input
                type="number"
                step="0.00000001"
                {...register("amount", { required: "Amount is required", valueAsNumber: true })}
              />
              {errors.amount && <span>{errors.amount.message}</span>}
            </div>
            {/* Source Selector */}
            <div>
              <label>Source:</label>
              <select {...register("source", { required: "Source is required" })}>
                <option value="N/A">N/A</option>
                <option value="My BTC">My BTC</option>
                <option value="Gift">Gift</option>
                <option value="Income">Income</option>
                <option value="Interest">Interest</option>
                <option value="Reward">Reward</option>
              </select>
              {errors.source && <span>{errors.source.message}</span>}
            </div>
            {/* Fee Field */}
            <div>
              <label>Fee:</label>
              <input type="number" step="0.00000001" {...register("fee", { valueAsNumber: true })} />
              <select {...register("feeCurrency")}>
                <option value="">Select Fee Currency</option>
                <option value="USD">USD</option>
                <option value="BTC">BTC</option>
              </select>
            </div>
          </div>
        );
      case "withdrawal":
        return (
          <div>
            <div>
              <label>Account:</label>
              <select {...register("account", { required: "Account is required" })}>
                <option value="">Select Account</option>
                <option value="bank">Bank</option>
                <option value="wallet">Wallet</option>
                <option value="exchange">Exchange</option>
              </select>
              {errors.account && <span>{errors.account.message}</span>}
            </div>
            <div>
              <label>Currency:</label>
              {account === "exchange" ? (
                <select {...register("currency", { required: "Currency is required" })}>
                  <option value="">Select Currency</option>
                  <option value="USD">USD</option>
                  <option value="BTC">BTC</option>
                </select>
              ) : (
                <input type="text" {...register("currency")} readOnly />
              )}
              {errors.currency && <span>{errors.currency.message}</span>}
            </div>
            <div>
              <label>Amount:</label>
              <input
                type="number"
                step="0.00000001"
                {...register("amount", { required: "Amount is required", valueAsNumber: true })}
              />
              {errors.amount && <span>{errors.amount.message}</span>}
            </div>
            <div>
              <label>Purpose:</label>
              <select {...register("purpose", { required: "Purpose is required" })}>
                <option value="N/A">N/A</option>
                <option value="Spent">Spent</option>
                <option value="Gift">Gift</option>
                <option value="Donation">Donation</option>
                <option value="Lost">Lost</option>
              </select>
              {errors.purpose && <span>{errors.purpose.message}</span>}
            </div>
            <div>
              <label>Fee:</label>
              <input type="number" step="0.00000001" {...register("fee", { valueAsNumber: true })} />
              <select {...register("feeCurrency")}>
                <option value="">Select Fee Currency</option>
                <option value="USD">USD</option>
                <option value="BTC">BTC</option>
              </select>
            </div>
          </div>
        );
        case "transfer":
  return (
    <div>
      {/* From Account */}
      <div>
        <label>From Account:</label>
        <select {...register("fromAccount", { required: "From Account is required" })}>
          <option value="">Select From Account</option>
          <option value="bank">Bank</option>
          <option value="wallet">Wallet</option>
          <option value="exchange">Exchange</option>
        </select>
        {errors.fromAccount && <span>{errors.fromAccount.message}</span>}
      </div>

      {/* From Currency */}
      <div>
        <label>From Currency:</label>
        {fromAccount === "exchange" ? (
          <select {...register("fromCurrency", { required: "From Currency is required" })}>
            <option value="">Select Currency</option>
            <option value="USD">USD</option>
            <option value="BTC">BTC</option>
          </select>
        ) : (
          <input type="text" {...register("fromCurrency")} readOnly />
        )}
        {errors.fromCurrency && <span>{errors.fromCurrency.message}</span>}
      </div>

      {/* Amount (From) */}
      <div>
        <label>Amount (From):</label>
        <input
          type="number"
          step="0.00000001"
          {...register("amountFrom", { required: "Amount (From) is required", valueAsNumber: true })}
        />
        {errors.amountFrom && <span>{errors.amountFrom.message}</span>}
      </div>

      {/* To Account */}
      <div>
        <label>To Account:</label>
        {fromAccount === "bank" || fromAccount === "wallet" ? (
          // For bank or wallet, the only option is to transfer to Exchange.
          <input type="text" value="Exchange" readOnly {...register("toAccount")} />
        ) : fromAccount === "exchange" ? (
          // For exchange, auto-set based on fromCurrency:
          <input
            type="text"
            value={fromCurrency === "USD" ? "Bank" : fromCurrency === "BTC" ? "Wallet" : ""}
            readOnly
            {...register("toAccount")}
          />
        ) : (
          <input type="text" value="" readOnly {...register("toAccount")} />
        )}
        {errors.toAccount && <span>{errors.toAccount.message}</span>}
      </div>

      {/* To Currency */}
      <div>
        <label>To Currency:</label>
        {(fromAccount === "bank" || fromAccount === "wallet" || fromAccount === "exchange") ? (
          // Auto-set to be the same as fromCurrency.
          <input type="text" value={fromCurrency || ""} readOnly {...register("toCurrency")} />
        ) : (
          <input type="text" value="" readOnly {...register("toCurrency")} />
        )}
        {errors.toCurrency && <span>{errors.toCurrency.message}</span>}
      </div>

      {/* Amount (To) */}
      <div>
        <label>Amount (To):</label>
        <input
          type="number"
          step="0.00000001"
          {...register("amountTo", { required: "Amount (To) is required", valueAsNumber: true })}
        />
        {errors.amountTo && <span>{errors.amountTo.message}</span>}
      </div>

      {/* Fee */}
      <div>
        <label>Fee:</label>
        <input type="number" step="0.00000001" {...register("fee", { valueAsNumber: true })} />
        <select {...register("feeCurrency")}>
          <option value="">Select Fee Currency</option>
          <option value="USD">USD</option>
          <option value="BTC">BTC</option>
        </select>
      </div>
    </div>
  );        
      case "buy":
        return (
          <div>
            <div>
              <label>Account:</label>
              <input type="text" value="Exchange" readOnly {...register("account")} />
            </div>
            <div>
              <label>Amount USD:</label>
              <input
                type="number"
                step="0.01"
                {...register("amountUSD", { required: "Amount USD is required", valueAsNumber: true })}
              />
              {errors.amountUSD && <span>{errors.amountUSD.message}</span>}
            </div>
            <div>
              <label>Amount BTC:</label>
              <input
                type="number"
                step="0.00000001"
                {...register("amountBTC", { required: "Amount BTC is required", valueAsNumber: true })}
              />
              {errors.amountBTC && <span>{errors.amountBTC.message}</span>}
            </div>
            <div>
              <label>Fee:</label>
              <input type="number" step="0.00000001" {...register("fee", { valueAsNumber: true })} />
              <select {...register("feeCurrency")}>
                <option value="">Select Fee Currency</option>
                <option value="USD">USD</option>
                <option value="BTC">BTC</option>
              </select>
            </div>
          </div>
        );
        case "sell":
          return (
            <div>
              <div>
                <label>Account:</label>
                <input type="text" value="Exchange" readOnly {...register("account")} />
              </div>
              {/* Removed the trade type toggle since it's not needed */}
              <div>
                <label>Amount BTC:</label>
                <input
                  type="number"
                  step="0.00000001"
                  {...register("amountBTC", { required: "Amount BTC is required", valueAsNumber: true })}
                />
                {errors.amountBTC && <span>{errors.amountBTC.message}</span>}
              </div>
              <div>
                <label>Amount USD:</label>
                <input
                  type="number"
                  step="0.01"
                  {...register("amountUSD", { required: "Amount USD is required", valueAsNumber: true })}
                />
                {errors.amountUSD && <span>{errors.amountUSD.message}</span>}
              </div>
              <div>
                <label>Fee:</label>
                <input type="number" step="0.00000001" {...register("fee", { valueAsNumber: true })} />
                <select {...register("feeCurrency")}>
                  <option value="">Select Fee Currency</option>
                  <option value="USD">USD</option>
                  <option value="BTC">BTC</option>
                </select>
              </div>
            </div>
          );        
      default:
        return null;
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <label>Transaction Type:</label>
        <select value={currentType} onChange={onTransactionTypeChange} required>
          <option value="">Select Transaction Type</option>
          <option value="deposit">Deposit</option>
          <option value="withdrawal">Withdrawal</option>
          <option value="transfer">Transfer</option>
          <option value="buy">Buy</option>
          <option value="sell">Sell</option>
        </select>
      </div>
      <div>
        <label>Date &amp; Time:</label>
        <input type="datetime-local" {...register("dateTime", { required: "Date & Time is required" })} />
        {errors.dateTime && <span>{errors.dateTime.message}</span>}
      </div>
      {renderDynamicFields()}
      <button type="submit">Submit Transaction</button>
    </form>
  );
};

export default TransactionForm;
