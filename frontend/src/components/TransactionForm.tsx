/**
 * TransactionForm.tsx
 *
 * This refactor keeps all original logic and comments, 
 * but integrates a "format.ts" helper file for decimal 
 * parsing and date conversions. 
 *
 * For example, instead of "let amount = data.amount || 0;", 
 * we now do "let amount = parseDecimal(data.amount);"
 * so that we consistently handle numeric fields even if 
 * user inputs are strings or partial decimals.
 */

import React, { useState, useEffect } from "react";
import { useForm, SubmitHandler } from "react-hook-form";
import axios from "axios";            // For isAxiosError checks
import api from "../api";             // Centralized API client
import "../styles/transactionForm.css";

// ------------------------------
//  1) IMPORTING HELPERS
// ------------------------------
// We only import parseDecimal here; localDatetimeToIso is a small local function
// defined below. parseDecimal ensures that user-typed numeric fields are 
// properly converted from string to number in the final payload.

import {
  parseDecimal
  // parseDecimal => ensures numeric fields like amount/fee 
  //   are consistently parsed from user input.
} from "../utils/format";

/**
 * A small local helper function that converts a "datetime-local" 
 * string (e.g. "2023-09-25T12:34") to a full ISO8601 format for the backend.
 * This replaces the missing `localDatetimeToIso` from your utils.
 */
function localDatetimeToIso(localDatetime: string): string {
  // You can customize how to handle the local time offset if needed.
  // For simplicity, we just do `new Date(localDatetime).toISOString()`.
  return new Date(localDatetime).toISOString();
}

/**
 * ------------------------------------------------------------
 * 1) Enumerations & Types for Frontend
 * ------------------------------------------------------------
 * We keep the same type definitions for a simpler user-facing UI.
 * Even though the backend uses multiple ledger lines, we only
 * display single 'amount' or 'fee' fields here. The services
 * handle the multi-line splitting automatically.
 */
type TransactionType = "Deposit" | "Withdrawal" | "Transfer" | "Buy" | "Sell";
type AccountType = "Bank" | "Wallet" | "Exchange";
type DepositSource = "N/A" | "MyBTC" | "Gift" | "Income" | "Interest" | "Reward";
type WithdrawalPurpose = "N/A" | "Spent" | "Gift" | "Donation" | "Lost";
type Currency = "USD" | "BTC";

/**
 * TransactionFormData:
 * Reflects the legacy single-entry fields. The user sees a single
 * 'amount' or 'fee' field, which the new double-entry backend will
 * transform into multiple ledger lines as needed.
 */
interface TransactionFormData {
  type: TransactionType;
  timestamp: string;

  // Single-account transactions
  account?: AccountType;
  currency?: Currency;
  amount?: number;
  source?: DepositSource;      // For BTC deposit
  purpose?: WithdrawalPurpose; // For BTC withdrawal
  fee?: number;               // We unify the numeric fee (BTC or USD)
  costBasisUSD?: number;      // For external BTC deposit or "Buy"

  // Transfer
  fromAccount?: AccountType;
  fromCurrency?: Currency;
  toAccount?: AccountType;
  toCurrency?: Currency;
  amountFrom?: number;  // from side (BTC or USD)
  amountTo?: number;    // to side (BTC or USD)

  // Added: proceeds_usd for BTC withdrawals or sells
  proceeds_usd?: number;

  // Buy/Sell
  amountUSD?: number;
  amountBTC?: number;
}

/**
 * ------------------------------------------------------------
 * 2) Hardcoded account ID mappings for demonstration
 * ------------------------------------------------------------
 * The new double-entry backend no longer depends on single-entry,
 * but we can still do these mappings for the user to choose.
 */
const EXTERNAL_ID = 99; // "External"
const EXCHANGE_USD_ID = 3;
const EXCHANGE_BTC_ID = 4;

/**
 * mapAccountToId:
 * For the user, we keep "Bank", "Wallet", "Exchange". The backend
 * uses numeric IDs. This function helps convert the UI selection
 * to a numeric ID. The new backend is flexible, but we keep these
 * mappings for a simpler UI approach.
 */
function mapAccountToId(account?: AccountType, currency?: Currency): number {
  if (account === "Bank") return 1;
  if (account === "Wallet") return 2;
  // "Exchange" => depends on currency
  if (account === "Exchange") {
    if (currency === "BTC") return EXCHANGE_BTC_ID;
    return EXCHANGE_USD_ID;
  }
  return 0;
}

/**
 * mapDoubleEntryAccounts:
 * Convert the user-chosen type ("Deposit", "Withdrawal", etc.)
 * plus optional UI fields (account, currency) into from_account_id
 * and to_account_id for the new transaction payload.
 */
function mapDoubleEntryAccounts(data: TransactionFormData): {
  from_account_id: number;
  to_account_id: number;
} {
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
 * ------------------------------------------------------------
 * 3) Component Props
 * ------------------------------------------------------------
 * Optional props for hooking into parent states or
 * success callbacks.
 */
interface TransactionFormProps {
  id?: string;
  onDirtyChange?: (dirty: boolean) => void;
  onSubmitSuccess?: () => void;
}

/**
 * ------------------------------------------------------------
 * 4) TransactionForm
 * ------------------------------------------------------------
 * The main form for recording transactions. We keep single-entry
 * style, letting the user pick "from" or "to" accounts, "amount",
 * "fee", etc. The final backend service splits these into ledger
 * lines and possibly updates BTC lots (if Buy/Sell).
 */
const TransactionForm: React.FC<TransactionFormProps> = ({
  id,
  onDirtyChange,
  onSubmitSuccess,
}) => {
  /**
   * useForm => track fields like 'type', 'timestamp', 'fee', etc.
   * We default the timestamp to "now" and fee to 0 for convenience.
   */
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
      // Added: Guarantee proceeds_usd starts at 0
      proceeds_usd: 0,
    },
  });

  // The currently selected type of transaction
  const [currentType, setCurrentType] = useState<TransactionType | "">("");

  // A local state for displaying an approximate fee in USD
  const [feeInUsdDisplay, setFeeInUsdDisplay] = useState<number>(0);

  /**
   * We watch certain fields for dynamic logic, especially for Transfers.
   */
  const amountFromVal = watch("amountFrom") || 0;
  const amountToVal = watch("amountTo") || 0;
  const fromCurrencyVal = watch("fromCurrency");

  // For deposit/withdrawal logic
  const account = watch("account");
  const currency = watch("currency");

  // For buy/sell
  const amountUsdVal = watch("amountUSD") || 0;
  const amountBtcVal = watch("amountBTC") || 0;

  /**
   * These useEffects log user inputs for debugging. 
   * They do not affect the double-entry logic; they are
   * simply ensuring TypeScript handles the watch variables.
   */
  useEffect(() => {
    console.log("User typed in amountUSD:", amountUsdVal);
  }, [amountUsdVal]);

  useEffect(() => {
    console.log("User typed in amountBTC:", amountBtcVal);
  }, [amountBtcVal]);

  // Let the parent know if the form is dirty.
  useEffect(() => {
    onDirtyChange?.(isDirty);
  }, [isDirty, onDirtyChange]);

  /**
   * If user picks "Deposit" or "Withdrawal",
   * auto-set currency if they choose "Bank" or "Wallet".
   */
  useEffect(() => {
    if (currentType === "Deposit" || currentType === "Withdrawal") {
      if (account === "Bank") {
        setValue("currency", "USD");
      } else if (account === "Wallet") {
        setValue("currency", "BTC");
      }
      // if they choose "Exchange", we let them pick manually
    }
  }, [account, currentType, setValue]);

  /**
   * Transfer logic: picking fromAccount => we auto-pick toAccount
   * and their corresponding currency.
   */
  const fromAccount = watch("fromAccount");
  useEffect(() => {
    if (currentType !== "Transfer") return;
    if (fromAccount === "Bank") {
      setValue("fromCurrency", "USD");
      setValue("toAccount", "Exchange");
      setValue("toCurrency", "USD");
    } else if (fromAccount === "Wallet") {
      setValue("fromCurrency", "BTC");
      setValue("toAccount", "Exchange");
      setValue("toCurrency", "BTC");
    } else if (fromAccount === "Exchange") {
      if (fromCurrencyVal === "USD") {
        setValue("toAccount", "Bank");
        setValue("toCurrency", "USD");
      } else if (fromCurrencyVal === "BTC") {
        setValue("toAccount", "Wallet");
        setValue("toCurrency", "BTC");
      }
    }
  }, [currentType, fromAccount, fromCurrencyVal, setValue]);

  /**
   * If user changes transaction type, we reset the form
   * (but keep the new type).
   */
  const onTransactionTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedType = e.target.value as TransactionType;
    setCurrentType(selectedType);
    reset({
      type: selectedType,
      timestamp: new Date().toISOString().slice(0, 16),
      fee: 0,
      costBasisUSD: 0,
      // Added: Keep proceeds_usd at 0 on reset
      proceeds_usd: 0,
    });
  };

  /**
   * Show costBasis only if user chooses:
   *   type=Deposit, currency=BTC, and account=Wallet or Exchange
   */
  const showCostBasisField =
    currentType === "Deposit" &&
    currency === "BTC" &&
    (account === "Wallet" || account === "Exchange");

  /**
   * Auto-calc fee for "Transfer" if fromCurrency is BTC.
   * If negative, clamp it to 0. Also show an approximate USD display
   * using a mock price.
   */
  useEffect(() => {
    if (currentType === "Transfer") {
      if (fromCurrencyVal !== "BTC") {
        // If it's not BTC, we won't auto-calc fee.
        return;
      }
      const calcFee = amountFromVal - amountToVal;
      if (calcFee < 0) {
        setValue("fee", 0);
      } else {
        const feeBtc = Number(calcFee.toFixed(8));
        setValue("fee", feeBtc);

        // approximate USD for user display
        const mockBtcPrice = 30000; // in real code, fetch from an API
        const approxUsd = feeBtc * mockBtcPrice;
        setFeeInUsdDisplay(Number(approxUsd.toFixed(2)));
      }
    }
  }, [currentType, fromCurrencyVal, amountFromVal, amountToVal, setValue]);

  /**
   * onSubmit => build final payload to pass to the new double-entry backend
   * where it becomes multiple ledger entries, plus optional BTC lot usage.
   *
   * Notice how we use parseDecimal(...) to ensure user-typed fields (which 
   * come in as strings or partial decimals) become real numeric fields 
   * in the final transactionPayload. That prevents issues if the user 
   * typed "50.00010000" or something similar.
   */
  const onSubmit: SubmitHandler<TransactionFormData> = async (data) => {
    // Added: if BTC Withdrawal => ensure proceeds_usd is a real number (default 0)
    if (data.type === "Withdrawal" && data.currency === "BTC" && !data.proceeds_usd) {
      data.proceeds_usd = 0;
    }

    // 1) from/to IDs
    const { from_account_id, to_account_id } = mapDoubleEntryAccounts(data);

    // --------------------------------------------------------------
    // Using our helper => convert "2023-09-25T12:34" to an ISO string.
    // The user picks "datetime-local", so we do localDatetimeToIso 
    // for consistent server handling.
    // --------------------------------------------------------------
    const isoTimestamp = localDatetimeToIso(data.timestamp);

    // 2) We unify legacy fields for the final request, 
    //    but now we parse them with parseDecimal to ensure 
    //    they become proper numeric types. 
    let amount = 0;
    let feeCurrency = "USD";
    let source: string | undefined = undefined;
    let purpose: string | undefined = undefined;
    let cost_basis_usd = 0;
    let proceeds_usd = undefined;

    switch (data.type) {
      case "Deposit": {
        // parseDecimal => ensures it’s a number, default 0 if invalid
        amount = parseDecimal(data.amount);
        feeCurrency = data.currency === "BTC" ? "BTC" : "USD";
        source = data.source && data.source !== "N/A" ? data.source : "N/A";
        if (showCostBasisField) {
          cost_basis_usd = parseDecimal(data.costBasisUSD);
        }
        break;
      }
      case "Withdrawal": {
        amount = parseDecimal(data.amount);
        feeCurrency = data.currency === "BTC" ? "BTC" : "USD";
        purpose = data.purpose && data.purpose !== "N/A" ? data.purpose : "N/A";
        // parseDecimal => ensures proceeds_usd is numeric
        proceeds_usd = parseDecimal(data.proceeds_usd);
        break;
      }
      case "Transfer": {
        // parseDecimal => handle from/to amounts as well
        amount = parseDecimal(data.amountFrom);
        if (data.fromCurrency === "BTC") feeCurrency = "BTC";
        else feeCurrency = "USD";
        break;
      }
      case "Buy": {
        amount = parseDecimal(data.amountBTC);
        feeCurrency = "USD";
        cost_basis_usd = parseDecimal(data.amountUSD);
        break;
      }
      
      case "Sell": {
        // user enters amountBTC
        amount = parseDecimal(data.amountBTC);
        feeCurrency = "USD";
        // parse the proceeds in USD
        proceeds_usd = parseDecimal(data.amountUSD);
        break;
      }
    }

    // 3) Build final payload
    const transactionPayload = {
      from_account_id,
      to_account_id,
      type: data.type,
      amount,
      timestamp: isoTimestamp,
      // parseDecimal => ensures fee is also converted if user typed partial decimals
      fee_amount: parseDecimal(data.fee), 
      fee_currency: feeCurrency,
      cost_basis_usd,
      proceeds_usd, // includes your new "Withdrawal" assignment
      source,
      purpose,
      is_locked: false,
    };

    // 4) POST to backend using the centralized api client with corrected path
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
   * -----------------------------------------------------------
   * 5) Dynamic Fields
   * -----------------------------------------------------------
   * Renders different inputs based on the selected transaction type.
   * The new double-entry backend doesn't require separate forms,
   * but we keep them for better UX clarity.
   */
  const renderDynamicFields = () => {
    switch (currentType) {
      case "Deposit": {
        // 1) Watch the currently selected account & currency
        const account = watch("account");     // Bank, Wallet, Exchange
        const currency = watch("currency");   // USD, BTC
      
        // 2) Only show "Source" if: account=Wallet OR (account=Exchange AND currency=BTC)
        const showSource =
          account === "Wallet" ||
          (account === "Exchange" && currency === "BTC");
      
        // 3) Show "Cost Basis (USD)" if deposit + BTC + (wallet or exchange)
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
                {...register("amount", { required: true, valueAsNumber: true })}
              />
              {errors.amount && (
                <span className="error-text">Amount is required</span>
              )}
            </div>
      
            {/* Conditionally render "Source" only if showSource is true */}
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
        // Watch the account/currency
        const account = watch("account");
        const currency = watch("currency");
      
        // Also keep the existing watchers for purpose/spent warning
        const purposeVal = watch("purpose");
        const proceedsUsdVal = watch("proceeds_usd") ?? 0;
      
        // Only show "Purpose" if: (account=Wallet) OR (account=Exchange & currency=BTC)
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
      
            {/* Conditionally show "Purpose" only if account=Wallet or (Exchange & BTC). */}
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
      
            {/* Proceeds (USD) if currency=BTC */}
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

      case "Transfer":
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
        // No type selected yet
        return null;
    }
  };

  /**
   * -----------------------------------------------------------
   * 6) Render
   * -----------------------------------------------------------
   * The main form includes a dropdown for transaction type
   * and dynamic fields based on that type. Submitting calls
   * onSubmit to POST to the new double-entry backend.
   */
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

        {/* Render dynamic fields for each transaction type */}
        {renderDynamicFields()}
      </div>
    </form>
  );
};

export default TransactionForm;
