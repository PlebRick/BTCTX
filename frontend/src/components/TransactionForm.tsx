/**
 * TransactionForm.tsx
 *
 * Pulls all domain-specific types (TransactionType, TransactionFormData, etc.)
 * from your global.d.ts. The only local interface below is TransactionFormProps,
 * which is purely a React prop type you can optionally move to global if desired.
 */

import React, { useState, useEffect } from "react";
import { useForm, SubmitHandler } from "react-hook-form";
import axios from "axios";   // For isAxiosError checks
import api from "../api";    // Centralized API client
import "../styles/transactionForm.css";
import { parseDecimal } from "../utils/format";

function localDatetimeToIso(localDatetime: string): string {
  return new Date(localDatetime).toISOString();
}

interface TransactionFormProps {
  id?: string;
  onDirtyChange?: (dirty: boolean) => void;
  onSubmitSuccess?: () => void;
}

// ------------------------------------------------------------
// Hardcoded numeric account ID mappings
// ------------------------------------------------------------
const EXTERNAL_ID = 99; // "External"
const EXCHANGE_USD_ID = 3;
const EXCHANGE_BTC_ID = 4;

/**
 * mapAccountToId:
 * Convert user-chosen (AccountType + Currency) -> numeric ID
 */
function mapAccountToId(account?: AccountType, currency?: Currency): number {
  if (account === "Bank") return 1;
  if (account === "Wallet") return 2;
  if (account === "Exchange") {
    return currency === "BTC" ? EXCHANGE_BTC_ID : EXCHANGE_USD_ID;
  }
  return 0;
}

/**
 * mapDoubleEntryAccounts:
 * Translates a single-entry TransactionFormData into from/to IDs
 * for the new double-entry backend payload.
 */
function mapDoubleEntryAccounts(data: TransactionFormData) {
  switch (data.type) {
    case "Deposit":
      return {
        from_account_id: EXTERNAL_ID,
        to_account_id: mapAccountToId(data.account, data.currency),
      };
    case "Withdrawal":
      return {
        from_account_id: mapAccountToId(data.account, data.currency),
        to_account_id: EXTERNAL_ID,
      };
    case "Transfer":
      return {
        from_account_id: mapAccountToId(data.fromAccount, data.fromCurrency),
        to_account_id: mapAccountToId(data.toAccount, data.toCurrency),
      };
    case "Buy":
      return {
        from_account_id: EXCHANGE_USD_ID,
        to_account_id: EXCHANGE_BTC_ID,
      };
    case "Sell":
      return {
        from_account_id: EXCHANGE_BTC_ID,
        to_account_id: EXCHANGE_USD_ID,
      };
    default:
      return { from_account_id: 0, to_account_id: 0 };
  }
}

/**
 * TransactionForm:
 * A single component that handles creating/editing a transaction
 * in "single-entry" style; behind the scenes, the new backend
 * interprets it as double-entry ledger lines, etc.
 */
const TransactionForm: React.FC<TransactionFormProps> = ({
  id,
  onDirtyChange,
  onSubmitSuccess,
}) => {
  
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors, isDirty },
  } = useForm<TransactionFormData>({
    defaultValues: {
      timestamp: new Date().toISOString().slice(0, 16),
      fee: 0,
      costBasisUSD: 0,
      proceeds_usd: 0,
    },
  });

  // 2) Local React states
  const [currentType, setCurrentType] = useState<TransactionType | "">("");
  const [feeInUsdDisplay, setFeeInUsdDisplay] = useState<number>(0);

  // 3) Watch specific fields for dynamic logic
  const amountFromVal = watch("amountFrom") || 0;
  const amountToVal = watch("amountTo") || 0;
  const fromCurrencyVal = watch("fromCurrency");
  const accountVal = watch("account");
  const currencyVal = watch("currency");
  const amountUsdVal = watch("amountUSD") || 0;
  const amountBtcVal = watch("amountBTC") || 0;
  const fromAccountVal = watch("fromAccount");

  // Debug logs
  useEffect(() => {
    console.log("User typed in amountUSD:", amountUsdVal);
  }, [amountUsdVal]);

  useEffect(() => {
    console.log("User typed in amountBTC:", amountBtcVal);
  }, [amountBtcVal]);

  // Notify parent if form dirty state changes
  useEffect(() => {
    onDirtyChange?.(isDirty);
  }, [isDirty, onDirtyChange]);

  /**
   * Auto-set currency if user picks "Bank" => "USD", or "Wallet" => "BTC"
   * for deposit/withdrawal. If "Exchange", user picks manually.
   */
  useEffect(() => {
    if (currentType === "Deposit" || currentType === "Withdrawal") {
      if (accountVal === "Bank") {
        setValue("currency", "USD");
      } else if (accountVal === "Wallet") {
        setValue("currency", "BTC");
      }
    }
  }, [accountVal, currentType, setValue]);

  /**
   * Transfer logic: picking fromAccount => auto-pick toAccount + currency
   */
  useEffect(() => {
    if (currentType !== "Transfer") return;

    if (fromAccountVal === "Bank") {
      setValue("fromCurrency", "USD");
      setValue("toAccount", "Exchange");
      setValue("toCurrency", "USD");
    } else if (fromAccountVal === "Wallet") {
      setValue("fromCurrency", "BTC");
      setValue("toAccount", "Exchange");
      setValue("toCurrency", "BTC");
    } else if (fromAccountVal === "Exchange") {
      if (fromCurrencyVal === "USD") {
        setValue("toAccount", "Bank");
        setValue("toCurrency", "USD");
      } else if (fromCurrencyVal === "BTC") {
        setValue("toAccount", "Wallet");
        setValue("toCurrency", "BTC");
      }
    }
  }, [currentType, fromAccountVal, fromCurrencyVal, setValue]);

  /**
   * Changing transaction type resets the form but keeps that new type
   */
  const onTransactionTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedType = e.target.value as TransactionType;
    setCurrentType(selectedType);
    reset({
      type: selectedType,
      timestamp: new Date().toISOString().slice(0, 16),
      fee: 0,
      costBasisUSD: 0,
      proceeds_usd: 0,
    });
  };

  /**
   * If deposit + BTC + (wallet/exchange) => show cost basis field
   */
  const showCostBasisField =
    currentType === "Deposit" &&
    currencyVal === "BTC" &&
    (accountVal === "Wallet" || accountVal === "Exchange");

  /**
   * Auto-calc fee for Transfer if fromCurrency=BTC
   * (fee = amountFrom - amountTo). If negative => 0
   * Also show approximate USD (mockBtcPrice=30000).
   */
  useEffect(() => {
    if (currentType === "Transfer" && fromCurrencyVal === "BTC") {
      const calcFee = amountFromVal - amountToVal;
      if (calcFee < 0) {
        setValue("fee", 0);
      } else {
        const feeBtc = Number(calcFee.toFixed(8));
        setValue("fee", feeBtc);
        const mockBtcPrice = 30000; // example
        const approxUsd = feeBtc * mockBtcPrice;
        setFeeInUsdDisplay(Number(approxUsd.toFixed(2)));
      }
    }
  }, [currentType, fromCurrencyVal, amountFromVal, amountToVal, setValue]);

  /**
   * onSubmit => build final payload for the new double-entry backend
   */
  const onSubmit: SubmitHandler<TransactionFormData> = async (data) => {
    // If user does a BTC withdrawal but no proceeds -> set to 0
    if (data.type === "Withdrawal" && data.currency === "BTC" && !data.proceeds_usd) {
      data.proceeds_usd = 0;
    }

    // get from/to account IDs
    const { from_account_id, to_account_id } = mapDoubleEntryAccounts(data);
    // convert local "datetime-local" to ISO string
    const isoTimestamp = localDatetimeToIso(data.timestamp);

    let amount = 0;
    let feeCurrency: Currency | "USD" | "BTC" = "USD";
    let source: string | undefined;
    let purpose: string | undefined;
    let cost_basis_usd = 0;
    let proceeds_usd: number | undefined = undefined;

    switch (data.type) {
      case "Deposit":
        amount = parseDecimal(data.amount);
        feeCurrency = data.currency === "BTC" ? "BTC" : "USD";
        source = data.source && data.source !== "N/A" ? data.source : "N/A";
        if (showCostBasisField) {
          cost_basis_usd = parseDecimal(data.costBasisUSD);
        }
        break;
      case "Withdrawal":
        amount = parseDecimal(data.amount);
        feeCurrency = data.currency === "BTC" ? "BTC" : "USD";
        purpose = data.purpose && data.purpose !== "N/A" ? data.purpose : "N/A";
        proceeds_usd = parseDecimal(data.proceeds_usd);
        break;
      case "Transfer":
        amount = parseDecimal(data.amountFrom);
        feeCurrency = data.fromCurrency === "BTC" ? "BTC" : "USD";
        break;
      case "Buy":
        amount = parseDecimal(data.amountBTC);
        feeCurrency = "USD";
        cost_basis_usd = parseDecimal(data.amountUSD);
        break;
      case "Sell":
        amount = parseDecimal(data.amountBTC);
        feeCurrency = "USD";
        proceeds_usd = parseDecimal(data.amountUSD);
        break;
    }

    const transactionPayload = {
      from_account_id,
      to_account_id,
      type: data.type,
      amount,
      timestamp: isoTimestamp,
      fee_amount: parseDecimal(data.fee),
      fee_currency: feeCurrency,
      cost_basis_usd,
      proceeds_usd,
      source,
      purpose,
      is_locked: false,
    };

    try {
      const response = await api.post("/transactions", transactionPayload);
      console.log("Transaction created:", response.data);

      reset();
      setCurrentType("");
      alert("Transaction created successfully!");
      onSubmitSuccess?.();
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        const msg = error.response?.data?.detail || error.message || "Error";
        alert(`Failed to create transaction: ${msg}`);
      } else if (error instanceof Error) {
        alert(`Failed to create transaction: ${error.message}`);
      } else {
        alert("An unexpected error occurred while creating the transaction.");
      }
    }
  };

  /**
   * renderDynamicFields:
   * Displays different fields depending on currentType.
   */
  const renderDynamicFields = () => {
    switch (currentType) {
      case "Deposit": {
        const account = watch("account");
        const currency = watch("currency");
        const showSource =
          account === "Wallet" ||
          (account === "Exchange" && currency === "BTC");
        const showCostBasisField =
          currentType === "Deposit" &&
          currency === "BTC" &&
          (account === "Wallet" || account === "Exchange");

        return (
          <>
            <div className="form-group">
              <label>Account:</label>
              <select
                className="form-control"
                {...register("account", { required: true })}
              >
                <option value="">Select Account</option>
                <option value="Bank">Bank Account</option>
                <option value="Wallet">Bitcoin Wallet</option>
                <option value="Exchange">Exchange</option>
              </select>
              {errors.account && (
                <span className="error-text">Please select an account</span>
              )}
            </div>

            <div className="form-group">
              <label>Currency:</label>
              {account === "Exchange" ? (
                <select
                  className="form-control"
                  {...register("currency", { required: true })}
                >
                  <option value="">Select Currency</option>
                  <option value="USD">USD</option>
                  <option value="BTC">BTC</option>
                </select>
              ) : (
                <input
                  type="text"
                  className="form-control"
                  {...register("currency")}
                  readOnly
                />
              )}
              {errors.currency && (
                <span className="error-text">Currency is required</span>
              )}
            </div>

            <div className="form-group">
              <label>Amount:</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("amount", {
                  required: true,
                  valueAsNumber: true,
                })}
              />
              {errors.amount && (
                <span className="error-text">Amount is required</span>
              )}
            </div>

            {showSource && (
              <div className="form-group">
                <label>Source:</label>
                <select
                  className="form-control"
                  {...register("source", { required: true })}
                >
                  <option value="N/A">N/A</option>
                  <option value="MyBTC">MyBTC</option>
                  <option value="Gift">Gift</option>
                  <option value="Income">Income</option>
                  <option value="Interest">Interest</option>
                  <option value="Reward">Reward</option>
                </select>
              </div>
            )}

            <div className="form-group">
              <label>Fee:</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("fee", { valueAsNumber: true })}
              />
            </div>

            {showCostBasisField && (
              <div className="form-group">
                <label>Cost Basis (USD):</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-control"
                  {...register("costBasisUSD", { valueAsNumber: true })}
                />
              </div>
            )}
          </>
        );
      }

      case "Withdrawal": {
        const account = watch("account");
        const currency = watch("currency");
        const purposeVal = watch("purpose");
        const proceedsUsdVal = watch("proceeds_usd") ?? 0;
        const showPurpose =
          account === "Wallet" ||
          (account === "Exchange" && currency === "BTC");

        return (
          <>
            <div className="form-group">
              <label>Account:</label>
              <select
                className="form-control"
                {...register("account", { required: true })}
              >
                <option value="">Select Account</option>
                <option value="Bank">Bank Account</option>
                <option value="Wallet">Bitcoin Wallet</option>
                <option value="Exchange">Exchange</option>
              </select>
              {errors.account && (
                <span className="error-text">Please select an account</span>
              )}
            </div>

            <div className="form-group">
              <label>Currency:</label>
              {account === "Exchange" ? (
                <select
                  className="form-control"
                  {...register("currency", { required: true })}
                >
                  <option value="">Select Currency</option>
                  <option value="USD">USD</option>
                  <option value="BTC">BTC</option>
                </select>
              ) : (
                <input
                  type="text"
                  className="form-control"
                  {...register("currency")}
                  readOnly
                />
              )}
              {errors.currency && (
                <span className="error-text">Currency is required</span>
              )}
            </div>

            <div className="form-group">
              <label>Amount:</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("amount", {
                  required: true,
                  valueAsNumber: true,
                })}
              />
              {errors.amount && (
                <span className="error-text">Amount is required</span>
              )}
            </div>

            {showPurpose && (
              <div className="form-group">
                <label>Purpose (BTC only):</label>
                <select
                  className="form-control"
                  {...register("purpose", { required: true })}
                >
                  <option value="">Select Purpose</option>
                  <option value="Spent">Spent</option>
                  <option value="Gift">Gift</option>
                  <option value="Donation">Donation</option>
                  <option value="Lost">Lost</option>
                </select>
              </div>
            )}

            <div className="form-group">
              <label>Fee:</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("fee", { valueAsNumber: true })}
              />
            </div>

            {currency === "BTC" && (
              <div className="form-group">
                <label>Proceeds (USD):</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-control"
                  defaultValue={0}
                  {...register("proceeds_usd", { valueAsNumber: true })}
                />
              </div>
            )}

            {currency === "BTC" &&
              purposeVal === "Spent" &&
              proceedsUsdVal === 0 && (
                <div style={{ color: "red", marginTop: "5px" }}>
                  <strong>Warning:</strong> You selected “Spent” but “Proceeds (USD)” is 0.
                </div>
            )}
          </>
        );
      }

      case "Transfer": {
        const fromAccount = watch("fromAccount");
        return (
          <>
            <div className="form-group">
              <label>From Account:</label>
              <select
                className="form-control"
                {...register("fromAccount", { required: true })}
              >
                <option value="">Select From Account</option>
                <option value="Bank">Bank Account</option>
                <option value="Wallet">Bitcoin Wallet</option>
                <option value="Exchange">Exchange</option>
              </select>
              {errors.fromAccount && (
                <span className="error-text">From Account is required</span>
              )}
            </div>

            <div className="form-group">
              <label>From Currency:</label>
              {fromAccount === "Exchange" ? (
                <select
                  className="form-control"
                  {...register("fromCurrency", { required: true })}
                >
                  <option value="">Select Currency</option>
                  <option value="USD">USD</option>
                  <option value="BTC">BTC</option>
                </select>
              ) : (
                <input
                  type="text"
                  className="form-control"
                  {...register("fromCurrency")}
                  readOnly
                />
              )}
              {errors.fromCurrency && (
                <span className="error-text">From Currency is required</span>
              )}
            </div>

            <div className="form-group">
              <label>Amount (From):</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("amountFrom", {
                  required: true,
                  valueAsNumber: true,
                })}
              />
              {errors.amountFrom && (
                <span className="error-text">Amount (From) is required</span>
              )}
            </div>

            <div className="form-group">
              <label>To Account:</label>
              <input
                type="text"
                className="form-control"
                {...register("toAccount")}
                readOnly
              />
            </div>

            <div className="form-group">
              <label>To Currency:</label>
              <input
                type="text"
                className="form-control"
                {...register("toCurrency")}
                readOnly
              />
            </div>

            <div className="form-group">
              <label>Amount (To):</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("amountTo", {
                  required: true,
                  valueAsNumber: true,
                })}
              />
              {errors.amountTo && (
                <span className="error-text">Amount (To) is required</span>
              )}
            </div>

            <div className="form-group">
              <label>Fee (BTC):</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("fee", { valueAsNumber: true })}
                readOnly
              />
              {feeInUsdDisplay > 0 && (
                <small style={{ color: "#bbb" }}>
                  (~ ${feeInUsdDisplay} USD)
                </small>
              )}
            </div>
          </>
        );
      }

      case "Buy":
        return (
          <>
            <div className="form-group">
              <label>Account:</label>
              <input
                type="text"
                className="form-control"
                value="Exchange"
                readOnly
                {...register("account")}
              />
            </div>

            <div className="form-group">
              <label>Amount USD:</label>
              <input
                type="number"
                step="0.01"
                className="form-control"
                {...register("amountUSD", {
                  required: true,
                  valueAsNumber: true,
                })}
              />
              {errors.amountUSD && (
                <span className="error-text">Amount USD is required</span>
              )}
            </div>

            <div className="form-group">
              <label>Amount BTC:</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("amountBTC", {
                  required: true,
                  valueAsNumber: true,
                })}
              />
              {errors.amountBTC && (
                <span className="error-text">Amount BTC is required</span>
              )}
            </div>

            <div className="form-group">
              <label>Fee (USD):</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("fee", { valueAsNumber: true })}
              />
            </div>
          </>
        );

      case "Sell":
        return (
          <>
            <div className="form-group">
              <label>Account:</label>
              <input
                type="text"
                className="form-control"
                value="Exchange"
                readOnly
                {...register("account")}
              />
            </div>

            <div className="form-group">
              <label>Amount BTC:</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("amountBTC", {
                  required: true,
                  valueAsNumber: true,
                })}
              />
              {errors.amountBTC && (
                <span className="error-text">Amount BTC is required</span>
              )}
            </div>

            <div className="form-group">
              <label>Amount USD:</label>
              <input
                type="number"
                step="0.01"
                className="form-control"
                {...register("amountUSD", {
                  required: true,
                  valueAsNumber: true,
                })}
              />
              {errors.amountUSD && (
                <span className="error-text">Amount USD is required</span>
              )}
            </div>

            <div className="form-group">
              <label>Fee (USD):</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("fee", { valueAsNumber: true })}
              />
            </div>
          </>
        );

      default:
        return null;
    }
  };

  // **Render** the main form
  return (
    <form
      id={id || "transaction-form"}
      className="transaction-form"
      onSubmit={handleSubmit(onSubmit)}
    >
      <div className="form-fields-grid">
        {/* Transaction type + timestamp */}
        <div className="form-group">
          <label>Transaction Type:</label>
          <select
            className="form-control"
            value={currentType}
            onChange={onTransactionTypeChange}
            required
          >
            <option value="">Select Transaction Type</option>
            <option value="Deposit">Deposit</option>
            <option value="Withdrawal">Withdrawal</option>
            <option value="Transfer">Transfer</option>
            <option value="Buy">Buy</option>
            <option value="Sell">Sell</option>
          </select>
        </div>

        <div className="form-group">
          <label>Date & Time:</label>
          <input
            type="datetime-local"
            className="form-control"
            {...register("timestamp", { required: "Date & Time is required" })}
          />
          {errors.timestamp && (
            <span className="error-text">{errors.timestamp.message}</span>
          )}
        </div>

        {/* Render the dynamic fields for each transaction type */}
        {renderDynamicFields()}
      </div>
    </form>
  );
};

export default TransactionForm;
