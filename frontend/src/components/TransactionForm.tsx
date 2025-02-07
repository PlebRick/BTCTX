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
// We add costBasisUSD to capture a manual cost basis for BTC deposits.
interface TransactionFormData {
  dateTime: string;
  transactionType: TransactionType;

  // Deposit/Withdrawal
  account?: AccountType;
  currency?: Currency;
  amount?: number;

  // Fee fields remain unchanged, but we keep them for reference:
  fee?: number;
  feeCurrency?: Currency;

  source?: DepositSource; // for deposits
  purpose?: WithdrawalPurpose; // for withdrawals

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
  tradeType?: "buy" | "sell"; // for Sell toggles, if needed

  // NEW: Only relevant if deposit + BTC
  costBasisUSD?: number;
}

const TransactionForm: React.FC = () => {
  /*
    useForm:
    - We set defaultValues so that the date/time field starts with the current UTC (truncated).
    - costBasisUSD is 0 by default; user can override only if it's a BTC deposit in a wallet/exchange.
  */
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<TransactionFormData>({
    defaultValues: {
      dateTime: new Date().toISOString().slice(0, 16), // "YYYY-MM-DDTHH:MM"
      costBasisUSD: 0, // By default, 0 cost basis unless user changes it
    },
  });

  // This local state tracks which transaction type is selected in the dropdown
  const [currentType, setCurrentType] = useState<TransactionType | "">("");

  // Watch these fields to trigger dynamic behaviors
  const account = watch("account");
  const fromAccount = watch("fromAccount");
  const toAccount = watch("toAccount");
  const currency = watch("currency"); // We'll need this for deposit logic

  /* 
    Auto-set the currency for deposit/withdrawal:
    - Bank => USD
    - Wallet => BTC
    - Exchange => user chooses from a dropdown
  */
  useEffect(() => {
    if (currentType === "deposit" || currentType === "withdrawal") {
      if (account === "bank") {
        setValue("currency", "USD");
      } else if (account === "wallet") {
        setValue("currency", "BTC");
      }
      // If account === "exchange", do nothing; user picks the currency manually
    }
  }, [account, currentType, setValue]);

  /*
    Auto-set currencies for Transfers:
    - If transferring from Bank => fromCurrency = USD
    - If from Wallet => fromCurrency = BTC
    - If from Exchange => user picks fromCurrency from [USD, BTC]
    - Then set toCurrency accordingly, e.g., if from "bank" => to "exchange" => possibly BTC, etc.
  */
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

  /*
    Whenever the user changes transaction type, we reset the form to fresh defaults,
    preserving the newly selected transactionType and a fresh dateTime. costBasisUSD
    is reset to 0 because it's only meaningful for BTC deposits to wallet/exchange.
  */
  const onTransactionTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedType = e.target.value as TransactionType;
    setCurrentType(selectedType);
    reset({
      transactionType: selectedType,
      dateTime: new Date().toISOString().slice(0, 16),
      costBasisUSD: 0,
    });
  };

  /*
    onSubmit:
    - If user is depositing BTC into wallet or exchange but doesn't enter costBasisUSD,
      we ensure it's 0 to avoid storing undefined or null.
    - Otherwise, just log the data (or post it to your backend).
  */
  const onSubmit: SubmitHandler<TransactionFormData> = (data) => {
    const isBTCDeposit =
      data.transactionType === "deposit" &&
      data.currency === "BTC" &&
      (data.account === "wallet" || data.account === "exchange");

    // If it's a BTC deposit and costBasis is missing/undefined, set to 0
    if (isBTCDeposit && !data.costBasisUSD) {
      data.costBasisUSD = 0;
    }

    console.log("Submitting transaction data:", data);
    // Replace with fetch/axios to POST to FastAPI when ready
  };

  /*
    We'll show a "Cost Basis (USD)" field only if:
      - transactionType == "deposit"
      - currency == "BTC"
      - account == "wallet" or "exchange"
  */
  const showCostBasisField =
    currentType === "deposit" &&
    currency === "BTC" &&
    (account === "wallet" || account === "exchange");

  /*
    Render dynamic fields:
    - We keep your existing cases for deposit, withdrawal, transfer, buy, sell exactly the same,
      only adding the cost basis field for deposit in the place you'd prefer.
  */
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

            {/* Currency: auto for bank/wallet, user-chosen if exchange */}
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
                {...register("amount", {
                  required: "Amount is required",
                  valueAsNumber: true,
                })}
              />
              {errors.amount && <span>{errors.amount.message}</span>}
            </div>

            {/* Source: user-chosen from N/A, My BTC, Gift, etc. */}
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

            {/* Fee: We do NOT change the existing logic for fees, just keep it as is. */}
            <div>
              <label>Fee:</label>
              <input
                type="number"
                step="0.00000001"
                {...register("fee", { valueAsNumber: true })}
              />
              <select {...register("feeCurrency")}>
                <option value="">Select Fee Currency</option>
                <option value="USD">USD</option>
                <option value="BTC">BTC</option>
              </select>
            </div>

            {/* If deposit + BTC + wallet or exchange => display costBasisUSD */}
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

      // The rest remain unchanged from your original code, only commented more thoroughly.

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
              <label>Fee:</label>
              <input
                type="number"
                step="0.00000001"
                {...register("fee", { valueAsNumber: true })}
              />
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
              <label>Fee:</label>
              <input
                type="number"
                step="0.00000001"
                {...register("fee", { valueAsNumber: true })}
              />
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
              <label>Fee:</label>
              <input
                type="number"
                step="0.00000001"
                {...register("fee", { valueAsNumber: true })}
              />
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
              <label>Fee:</label>
              <input
                type="number"
                step="0.00000001"
                {...register("fee", { valueAsNumber: true })}
              />
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
      {/* Transaction Type dropdown */}
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

      {/* Date & Time field */}
      <div>
        <label>Date &amp; Time:</label>
        <input
          type="datetime-local"
          {...register("dateTime", { required: "Date & Time is required" })}
        />
        {errors.dateTime && <span>{errors.dateTime.message}</span>}
      </div>

      {/* Render transaction-specific fields */}
      {renderDynamicFields()}

      {/* Submit */}
      <button type="submit">Submit Transaction</button>
    </form>
  );
};

export default TransactionForm;
