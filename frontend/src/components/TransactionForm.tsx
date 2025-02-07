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
// Fee is now always in USD, so no feeCurrency anymore.
interface TransactionFormData {
  dateTime: string;
  transactionType: TransactionType;

  // Deposit/Withdrawal
  account?: AccountType;
  currency?: Currency;
  amount?: number;

  // Fee is USD only
  fee?: number;

  // For deposit
  source?: DepositSource;

  // For withdrawal
  purpose?: WithdrawalPurpose;

  // Transfer
  fromAccount?: AccountType;
  fromCurrency?: Currency;
  amountFrom?: number;
  toAccount?: AccountType;
  toCurrency?: Currency;
  amountTo?: number;

  // Buy/Sell
  amountUSD?: number;
  amountBTC?: number;
  tradeType?: "buy" | "sell";

  // Show a manual cost basis for BTC deposits
  costBasisUSD?: number;
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
      dateTime: new Date().toISOString().slice(0, 16),
      fee: 0.0,
      costBasisUSD: 0.0,
    },
  });

  // Track the currently selected transaction type
  const [currentType, setCurrentType] = useState<TransactionType | "">("");

  // Watch fields for dynamic behavior
  const account = watch("account");
  const currency = watch("currency"); // Important for deciding if cost basis is needed
  const fromAccount = watch("fromAccount");
  const toAccount = watch("toAccount");

  // Auto-set currency for deposit/withdrawal based on account
  useEffect(() => {
    if (currentType === "deposit" || currentType === "withdrawal") {
      if (account === "bank") {
        setValue("currency", "USD");
      } else if (account === "wallet") {
        setValue("currency", "BTC");
      }
      // If account === "exchange", user chooses (no auto-set)
    }
  }, [account, currentType, setValue]);

  // Auto-set fromCurrency/toCurrency for transfers
  useEffect(() => {
    if (currentType === "transfer") {
      if (fromAccount === "bank") {
        setValue("fromCurrency", "USD");
      } else if (fromAccount === "wallet") {
        setValue("fromCurrency", "BTC");
      }
      // If fromAccount === "exchange", user chooses the fromCurrency
      if (toAccount === "bank") {
        setValue("toCurrency", "USD");
      } else if (toAccount === "wallet") {
        setValue("toCurrency", "BTC");
      }
      // If toAccount === "exchange", user might choose the toCurrency (but in this code
      // we auto-fill it below in the transfer fields, readOnly).
    }
  }, [fromAccount, toAccount, currentType, setValue]);

  // On transaction type change, reset form but preserve new type & fresh date/time
  const onTransactionTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedType = e.target.value as TransactionType;
    setCurrentType(selectedType);
    reset({
      transactionType: selectedType,
      dateTime: new Date().toISOString().slice(0, 16),
      fee: 0.0,
      costBasisUSD: 0.0,
    });
  };

  // Decide whether to show Cost Basis field
  // Only if deposit + BTC + wallet/exchange
  const showCostBasisField =
    currentType === "deposit" &&
    currency === "BTC" &&
    (account === "wallet" || account === "exchange");

  // Handle form submission
  const onSubmit: SubmitHandler<TransactionFormData> = (data) => {
    // If deposit is BTC into wallet or exchange, and costBasisUSD is undefined, set it to 0
    const isBTCDeposit =
      data.transactionType === "deposit" &&
      data.currency === "BTC" &&
      (data.account === "wallet" || data.account === "exchange");

    if (isBTCDeposit && !data.costBasisUSD) {
      data.costBasisUSD = 0;
    }

    console.log("Submitting transaction data:", data);
    // Replace with an API call to your FastAPI backend, e.g.:
    // axios.post('/api/transactions', data).then(...).catch(...);
  };

  // Renders the type-specific fields
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
            {/* Currency */}
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
            {/* Amount */}
            <div>
              <label>Amount:</label>
              <input
                type="number"
                step="0.00000001"
                {...register("amount", {
                  required: "Amount is required",
                  valueAsNumber: true,
                })}
              />
              {errors.amount && <span>{errors.amount.message}</span>}
            </div>
            {/* Source */}
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
            {/* Fee (USD only) */}
            <div>
              <label>Fee (USD):</label>
              <input type="number" step="0.01" {...register("fee", { valueAsNumber: true })} />
            </div>
            {/* Cost Basis if depositing BTC to wallet/exchange */}
            {showCostBasisField && (
              <div>
                <label>Cost Basis (USD):</label>
                <input
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  {...register("costBasisUSD", { valueAsNumber: true })}
                />
              </div>
            )}
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
                {...register("amount", {
                  required: "Amount is required",
                  valueAsNumber: true,
                })}
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
              <label>Fee (USD):</label>
              <input type="number" step="0.01" {...register("fee", { valueAsNumber: true })} />
            </div>
          </div>
        );

      case "transfer":
        return (
          <div>
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
            <div>
              <label>Amount (From):</label>
              <input
                type="number"
                step="0.00000001"
                {...register("amountFrom", {
                  required: "Amount (From) is required",
                  valueAsNumber: true,
                })}
              />
              {errors.amountFrom && <span>{errors.amountFrom.message}</span>}
            </div>
            <div>
              <label>To Account:</label>
              {fromAccount === "bank" || fromAccount === "wallet" ? (
                <input type="text" value="Exchange" readOnly {...register("toAccount")} />
              ) : fromAccount === "exchange" ? (
                <input
                  type="text"
                  value={
                    watch("fromCurrency") === "USD"
                      ? "Bank"
                      : watch("fromCurrency") === "BTC"
                      ? "Wallet"
                      : ""
                  }
                  readOnly
                  {...register("toAccount")}
                />
              ) : (
                <input type="text" value="" readOnly {...register("toAccount")} />
              )}
              {errors.toAccount && <span>{errors.toAccount.message}</span>}
            </div>
            <div>
              <label>To Currency:</label>
              {(fromAccount === "bank" ||
                fromAccount === "wallet" ||
                fromAccount === "exchange") ? (
                <input
                  type="text"
                  value={watch("fromCurrency") || ""}
                  readOnly
                  {...register("toCurrency")}
                />
              ) : (
                <input type="text" value="" readOnly {...register("toCurrency")} />
              )}
              {errors.toCurrency && <span>{errors.toCurrency.message}</span>}
            </div>
            <div>
              <label>Amount (To):</label>
              <input
                type="number"
                step="0.00000001"
                {...register("amountTo", {
                  required: "Amount (To) is required",
                  valueAsNumber: true,
                })}
              />
              {errors.amountTo && <span>{errors.amountTo.message}</span>}
            </div>
            <div>
              <label>Fee (USD):</label>
              <input type="number" step="0.01" {...register("fee", { valueAsNumber: true })} />
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
                {...register("amountUSD", {
                  required: "Amount USD is required",
                  valueAsNumber: true,
                })}
              />
              {errors.amountUSD && <span>{errors.amountUSD.message}</span>}
            </div>
            <div>
              <label>Amount BTC:</label>
              <input
                type="number"
                step="0.00000001"
                {...register("amountBTC", {
                  required: "Amount BTC is required",
                  valueAsNumber: true,
                })}
              />
              {errors.amountBTC && <span>{errors.amountBTC.message}</span>}
            </div>
            <div>
              <label>Fee (USD):</label>
              <input type="number" step="0.01" {...register("fee", { valueAsNumber: true })} />
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
            <div>
              <label>Amount BTC:</label>
              <input
                type="number"
                step="0.00000001"
                {...register("amountBTC", {
                  required: "Amount BTC is required",
                  valueAsNumber: true,
                })}
              />
              {errors.amountBTC && <span>{errors.amountBTC.message}</span>}
            </div>
            <div>
              <label>Amount USD:</label>
              <input
                type="number"
                step="0.01"
                {...register("amountUSD", {
                  required: "Amount USD is required",
                  valueAsNumber: true,
                })}
              />
              {errors.amountUSD && <span>{errors.amountUSD.message}</span>}
            </div>
            <div>
              <label>Fee (USD):</label>
              <input type="number" step="0.01" {...register("fee", { valueAsNumber: true })} />
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* Transaction Type */}
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

      {/* Date & Time */}
      <div>
        <label>Date &amp; Time:</label>
        <input
          type="datetime-local"
          {...register("dateTime", { required: "Date & Time is required" })}
        />
        {errors.dateTime && <span>{errors.dateTime.message}</span>}
      </div>

      {/* Render the transaction-specific fields */}
      {renderDynamicFields()}

      <button type="submit">Submit Transaction</button>
    </form>
  );
};

export default TransactionForm;