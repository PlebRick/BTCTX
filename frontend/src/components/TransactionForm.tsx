import React, { useState, useEffect } from "react";
import { useForm, SubmitHandler } from "react-hook-form";
import axios from "axios";
import "../styles/transactionForm.css";

/**
 * -----------------------------------------------------------
 * 1) Enumerations & Types
 * -----------------------------------------------------------
 * 
 * These define:
 * - The allowed transaction/account enums
 * - The shape of the form data (TransactionFormData)
 */

// Possible transaction types recognized by the app.
type TransactionType = "Deposit" | "Withdrawal" | "Transfer" | "Buy" | "Sell";

// Possible account types in the system.
type AccountType = "Bank" | "Wallet" | "Exchange";

// Additional dropdown enumerations for deposit/withdrawal.
type DepositSource = "N/A" | "My BTC" | "Gift" | "Income" | "Interest" | "Reward";
type WithdrawalPurpose = "N/A" | "Spent" | "Gift" | "Donation" | "Lost";
type Currency = "USD" | "BTC";

/**
 * The full shape of the data we collect from the TransactionForm.
 * Each transaction type reuses a subset of these fields:
 * - Common fields for deposit/withdrawal (account, currency, amount, fee, etc.)
 * - Transfer-only fields (fromAccount, fromCurrency, amountFrom, etc.)
 * - Buy/Sell fields (amountUSD, amountBTC)
 */
interface TransactionFormData {
  // Basic
  type: TransactionType;      
  timestamp: string;           // local date/time input, converted to ISO on submit
  account?: AccountType;       
  currency?: Currency;         
  amount?: number;             
  source?: DepositSource;      
  purpose?: WithdrawalPurpose; 
  fee?: number;                
  costBasisUSD?: number;       // used if depositing BTC

  // Transfer
  fromAccount?: AccountType;
  fromCurrency?: Currency;
  toAccount?: AccountType;
  toCurrency?: Currency;
  amountFrom?: number;
  amountTo?: number;

  // Buy/Sell
  amountUSD?: number;
  amountBTC?: number;
}

/**
 * Label dictionaries for dropdown usage 
 * (transactionTypeLabels, accountLabels).
 */
const transactionTypeLabels: Record<TransactionType, string> = {
  Deposit: "Deposit",
  Withdrawal: "Withdrawal",
  Transfer: "Transfer",
  Buy: "Buy",
  Sell: "Sell",
};
const accountLabels: Record<AccountType, string> = {
  Bank: "Bank Account",
  Wallet: "Bitcoin Wallet",
  Exchange: "Exchange",
};

/**
 * Helper: map an AccountType string to a numeric ID your backend uses.
 */
function mapAccountToId(account?: AccountType): number {
  switch (account) {
    case "Bank":
      return 1;
    case "Wallet":
      return 2;
    case "Exchange":
      return 3;
    default:
      return 0; // fallback if undefined/unknown
  }
}

/**
 * -----------------------------------------------------------
 * 2) Props for TransactionForm
 * -----------------------------------------------------------
 * - 'id' allows an external <button form=...> to submit this form
 * - 'onDirtyChange' notifies parent if the form is dirty
 * - 'onSubmitSuccess' fires after a successful POST
 */
interface TransactionFormProps {
  id?: string;
  onDirtyChange?: (dirty: boolean) => void;
  onSubmitSuccess?: () => void;
}

/**
 * -----------------------------------------------------------
 * 3) TransactionForm Component
 * -----------------------------------------------------------
 * Manages the UI for creating new transactions or editing existing ones.
 * Uses react-hook-form for data handling and validation.
 */
const TransactionForm: React.FC<TransactionFormProps> = ({
  id,
  onDirtyChange,
  onSubmitSuccess,
}) => {
  /**
   * -----------------------------------------------------------
   * 3A) React-Hook-Form Setup
   * -----------------------------------------------------------
   * 'defaultValues' sets initial form field values. 
   * We default 'timestamp' to now, 'fee' and 'costBasisUSD' to 0.
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
      timestamp: new Date().toISOString().slice(0, 16), // local datetime
      fee: 0,
      costBasisUSD: 0,
    },
  });

  /**
   * We'll keep track of the chosen transaction type in this local state,
   * so we can render the correct dynamic fields (Deposit vs Withdrawal, etc.).
   */
  const [currentType, setCurrentType] = useState<TransactionType | "">("");

  // Watch certain fields to implement dynamic logic:
  const account = watch("account");          // e.g. Bank, Wallet, Exchange
  const currency = watch("currency");        // e.g. USD, BTC
  const fromAccount = watch("fromAccount");  // used in Transfer logic
  const fromCurrencyVal = watch("fromCurrency");

  /**
   * -----------------------------------------------------------
   * 3B) Track dirty state changes
   * -----------------------------------------------------------
   * If the form is dirty, notify the parent. 
   * The parent might show a discard-changes modal, etc.
   */
  useEffect(() => {
    onDirtyChange?.(isDirty);
  }, [isDirty, onDirtyChange]);

  /**
   * -----------------------------------------------------------
   * 3C) Auto-set currency for Deposit/Withdrawal
   * -----------------------------------------------------------
   * If user picks 'Bank' for a Deposit, we auto-set currency=USD.
   * If user picks 'Wallet', currency=BTC. 
   * For 'Exchange', the user must pick manually.
   */
  useEffect(() => {
    if (currentType === "Deposit" || currentType === "Withdrawal") {
      if (account === "Bank") {
        setValue("currency", "USD");
      } else if (account === "Wallet") {
        setValue("currency", "BTC");
      }
    }
  }, [account, currentType, setValue]);

  /**
   * -----------------------------------------------------------
   * 3D) Auto-set from/to for Transfers
   * -----------------------------------------------------------
   * If 'fromAccount' is Bank => fromCurrency=USD => toAccount=Exchange => toCurrency=USD, etc.
   * If 'fromAccount' is Exchange => we look at fromCurrency to decide toAccount=Bank/Wallet.
   */
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
   * -----------------------------------------------------------
   * 3E) onTransactionTypeChange
   * -----------------------------------------------------------
   * If the user picks a new transaction type, we reset
   * the form to default. 
   */
  const onTransactionTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedType = e.target.value as TransactionType;
    setCurrentType(selectedType);
    reset({
      type: selectedType,
      timestamp: new Date().toISOString().slice(0, 16),
      fee: 0,
      costBasisUSD: 0,
    });
  };

  /**
   * -----------------------------------------------------------
   * 3F) showCostBasisField
   * -----------------------------------------------------------
   * We only show the cost basis input if it's a BTC deposit 
   * into a Wallet or Exchange.
   */
  const showCostBasisField =
    currentType === "Deposit" &&
    currency === "BTC" &&
    (account === "Wallet" || account === "Exchange");

  /**
   * -----------------------------------------------------------
   * 3G) onSubmit
   * -----------------------------------------------------------
   * Called when the user submits the form. We build the payload
   * expected by the backend, then POST to create a new transaction.
   */
  const onSubmit: SubmitHandler<TransactionFormData> = async (data) => {
    // Convert local date/time to an ISO string
    const isoTimestamp = new Date(data.timestamp).toISOString();

    // We'll calculate amountUSD, amountBTC, source, purpose, accountId based on type
    let amountUSD = 0.0;
    let amountBTC = 0.0;
    let source = "N/A";
    let purpose = "N/A";
    let accountId = 0;

    // Decide which fields to fill
    switch (data.type) {
      case "Deposit": {
        accountId = mapAccountToId(data.account);
        if (data.currency === "USD") {
          amountUSD = data.amount || 0;
        } else {
          amountBTC = data.amount || 0;
        }
        source = data.source || "N/A";
        break;
      }
      case "Withdrawal": {
        accountId = mapAccountToId(data.account);
        if (data.currency === "USD") {
          amountUSD = data.amount || 0;
        } else {
          amountBTC = data.amount || 0;
        }
        purpose = data.purpose || "N/A";
        break;
      }
      case "Transfer": {
        // For a transfer, the "from" side is tracked in this record
        accountId = mapAccountToId(data.fromAccount);
        if (data.fromCurrency === "USD") {
          amountUSD = data.amountFrom || 0;
        } else {
          amountBTC = data.amountFrom || 0;
        }
        break;
      }
      case "Buy":
      case "Sell": {
        // Always Exchange
        accountId = 3;
        amountUSD = data.amountUSD || 0;
        amountBTC = data.amountBTC || 0;
        break;
      }
    }

    // If it's a BTC deposit, we might have a cost basis from the user
    const finalCostBasis = showCostBasisField ? (data.costBasisUSD || 0) : 0;

    // Build the payload
    const transactionPayload = {
      account_id: accountId,
      type: data.type,
      amount_usd: amountUSD,
      amount_btc: amountBTC,
      timestamp: isoTimestamp,
      source,
      purpose,
      fee: data.fee || 0,
      cost_basis_usd: finalCostBasis,
      is_locked: false,
    };

    // POST to your backend
    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/api/transactions",
        transactionPayload
      );
      console.log("Transaction created:", response.data);

      // Reset form + notify user
      reset();
      setCurrentType("");
      alert("Transaction created successfully!");

      // If parent wants to refresh or close, call it
      onSubmitSuccess?.();
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        const message =
          error.response?.data?.detail || error.message || "An error occurred";
        alert(`Failed to create transaction: ${message}`);
      } else if (error instanceof Error) {
        alert(`Failed to create transaction: ${error.message}`);
      } else {
        alert("An unexpected error occurred while creating the transaction.");
      }
    }
  };

  /**
   * -----------------------------------------------------------
   * 3H) renderDynamicFields
   * -----------------------------------------------------------
   * Based on currentType, render the appropriate fields:
   * - Deposit => account, currency, amount, source, fee, etc.
   * - Withdrawal => account, currency, amount, purpose, fee, etc.
   * - Transfer => fromAccount, toAccount, etc.
   * - Buy/Sell => exchange fields for USD + BTC amounts
   */
  const renderDynamicFields = () => {
    switch (currentType) {
      case "Deposit":
        return (
          <>
            {/* Account */}
            <div className="form-group">
              <label>Account:</label>
              <select
                className="form-control"
                {...register("account", { required: true })}
              >
                <option value="">Select Account</option>
                {Object.entries(accountLabels).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
              {errors.account && (
                <span className="error-text">Please select an account</span>
              )}
            </div>

            {/* Currency */}
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

            {/* Amount */}
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

            {/* Source */}
            <div className="form-group">
              <label>Source:</label>
              <select
                className="form-control"
                {...register("source", { required: true })}
              >
                <option value="N/A">N/A</option>
                <option value="My BTC">My BTC</option>
                <option value="Gift">Gift</option>
                <option value="Income">Income</option>
                <option value="Interest">Interest</option>
                <option value="Reward">Reward</option>
              </select>
              {errors.source && (
                <span className="error-text">Source is required</span>
              )}
            </div>

            {/* Fee (USD) */}
            <div className="form-group">
              <label>Fee (USD):</label>
              <input
                type="number"
                step="0.01"
                className="form-control"
                {...register("fee", { valueAsNumber: true })}
              />
            </div>

            {/* Optional Cost Basis if BTC */}
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

      case "Withdrawal":
        return (
          <>
            {/* Account */}
            <div className="form-group">
              <label>Account:</label>
              <select
                className="form-control"
                {...register("account", { required: true })}
              >
                <option value="">Select Account</option>
                {Object.entries(accountLabels).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
              {errors.account && (
                <span className="error-text">Please select an account</span>
              )}
            </div>

            {/* Currency */}
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

            {/* Amount */}
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

            {/* Purpose */}
            <div className="form-group">
              <label>Purpose:</label>
              <select
                className="form-control"
                {...register("purpose", { required: true })}
              >
                <option value="N/A">N/A</option>
                <option value="Spent">Spent</option>
                <option value="Gift">Gift</option>
                <option value="Donation">Donation</option>
                <option value="Lost">Lost</option>
              </select>
              {errors.purpose && (
                <span className="error-text">Purpose is required</span>
              )}
            </div>

            {/* Fee (USD) */}
            <div className="form-group">
              <label>Fee (USD):</label>
              <input
                type="number"
                step="0.01"
                className="form-control"
                {...register("fee", { valueAsNumber: true })}
              />
            </div>
          </>
        );

      case "Transfer":
        return (
          <>
            {/* From Account */}
            <div className="form-group">
              <label>From Account:</label>
              <select
                className="form-control"
                {...register("fromAccount", { required: true })}
              >
                <option value="">Select From Account</option>
                {Object.entries(accountLabels).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
              {errors.fromAccount && (
                <span className="error-text">From Account is required</span>
              )}
            </div>

            {/* From Currency */}
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

            {/* Amount (From) */}
            <div className="form-group">
              <label>Amount (From):</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("amountFrom", { required: true, valueAsNumber: true })}
              />
              {errors.amountFrom && (
                <span className="error-text">Amount (From) is required</span>
              )}
            </div>

            {/* To Account (read-only, auto-filled) */}
            <div className="form-group">
              <label>To Account:</label>
              <input
                type="text"
                className="form-control"
                {...register("toAccount")}
                readOnly
              />
            </div>

            {/* To Currency (read-only, auto-filled) */}
            <div className="form-group">
              <label>To Currency:</label>
              <input
                type="text"
                className="form-control"
                {...register("toCurrency")}
                readOnly
              />
            </div>

            {/* Amount (To) */}
            <div className="form-group">
              <label>Amount (To):</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("amountTo", { required: true, valueAsNumber: true })}
              />
              {errors.amountTo && (
                <span className="error-text">Amount (To) is required</span>
              )}
            </div>

            {/* Fee in USD */}
            <div className="form-group">
              <label>Fee (USD):</label>
              <input
                type="number"
                step="0.01"
                className="form-control"
                {...register("fee", { valueAsNumber: true })}
              />
            </div>
          </>
        );

      case "Buy":
        return (
          <>
            {/* Account is always Exchange */}
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

            {/* Amount USD */}
            <div className="form-group">
              <label>Amount USD:</label>
              <input
                type="number"
                step="0.01"
                className="form-control"
                {...register("amountUSD", { required: true, valueAsNumber: true })}
              />
              {errors.amountUSD && (
                <span className="error-text">Amount USD is required</span>
              )}
            </div>

            {/* Amount BTC */}
            <div className="form-group">
              <label>Amount BTC:</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("amountBTC", { required: true, valueAsNumber: true })}
              />
              {errors.amountBTC && (
                <span className="error-text">Amount BTC is required</span>
              )}
            </div>

            {/* Fee (USD) */}
            <div className="form-group">
              <label>Fee (USD):</label>
              <input
                type="number"
                step="0.01"
                className="form-control"
                {...register("fee", { valueAsNumber: true })}
              />
            </div>
          </>
        );

      case "Sell":
        return (
          <>
            {/* Account is always Exchange */}
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

            {/* Amount BTC */}
            <div className="form-group">
              <label>Amount BTC:</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("amountBTC", { required: true, valueAsNumber: true })}
              />
              {errors.amountBTC && (
                <span className="error-text">Amount BTC is required</span>
              )}
            </div>

            {/* Amount USD */}
            <div className="form-group">
              <label>Amount USD:</label>
              <input
                type="number"
                step="0.01"
                className="form-control"
                {...register("amountUSD", { required: true, valueAsNumber: true })}
              />
              {errors.amountUSD && (
                <span className="error-text">Amount USD is required</span>
              )}
            </div>

            {/* Fee (USD) */}
            <div className="form-group">
              <label>Fee (USD):</label>
              <input
                type="number"
                step="0.01"
                className="form-control"
                {...register("fee", { valueAsNumber: true })}
              />
            </div>
          </>
        );

      default:
        // If the user hasn't selected a type yet, or it's unknown
        return null;
    }
  };

  /**
   * -----------------------------------------------------------
   * 3I) Render
   * -----------------------------------------------------------
   * We place all form fields in a grid layout (transaction-form + form-fields-grid).
   * The parent panel can submit this form by referencing id={id}.
   */
  return (
    <form
      id={id || "transactionFormId"} // in case the panel's save button uses form="transactionFormId"
      className="transaction-form"
      onSubmit={handleSubmit(onSubmit)}
    >
      <div className="form-fields-grid">
        {/* Top row: transaction type + date/time */}
        <div className="form-group">
          <label>Transaction Type:</label>
          <select
            className="form-control"
            value={currentType}
            onChange={onTransactionTypeChange}
            required
          >
            <option value="">Select Transaction Type</option>
            {Object.entries(transactionTypeLabels).map(([typeEnum, label]) => (
              <option key={typeEnum} value={typeEnum}>
                {label}
              </option>
            ))}
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

        {/* Dynamic fields for deposit/withdrawal/transfer/buy/sell */}
        {renderDynamicFields()}

        {/*
          (Optional) If you want an internal submit button:
          <div className="form-group" style={{ gridColumn: "1 / -1" }}>
            <button type="submit" className="submit-button">
              Submit Transaction
            </button>
          </div>
        */}
      </div>
    </form>
  );
};

export default TransactionForm;