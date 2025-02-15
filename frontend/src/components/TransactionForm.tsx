import React, { useState, useEffect } from "react";
import { useForm, SubmitHandler } from "react-hook-form";
import axios from "axios";
import "../styles/transactionForm.css"; // Import your updated CSS with the .form-fields-grid class

// --------------------------------------------------
// 1) TypeScript Types & Enums (Matching the Backend)
// --------------------------------------------------
type TransactionType = "Deposit" | "Withdrawal" | "Transfer" | "Buy" | "Sell";

type AccountType = "Bank" | "Wallet" | "Exchange";

type DepositSource = "N/A" | "My BTC" | "Gift" | "Income" | "Interest" | "Reward";
type WithdrawalPurpose = "N/A" | "Spent" | "Gift" | "Donation" | "Lost";
type Currency = "USD" | "BTC";

// The shape of the form data we'll capture
interface TransactionFormData {
  // Basic fields
  type: TransactionType;
  timestamp: string; // We'll convert to ISO string for the backend
  account?: AccountType;
  currency?: Currency;
  amount?: number;
  source?: DepositSource;
  purpose?: WithdrawalPurpose;
  fee?: number; // Always in USD
  costBasisUSD?: number; // For BTC deposits

  // Transfer fields
  fromAccount?: AccountType;
  fromCurrency?: Currency;
  toAccount?: AccountType;
  toCurrency?: Currency;
  amountFrom?: number;
  amountTo?: number;

  // Buy/Sell fields
  amountUSD?: number;
  amountBTC?: number;
}

// --------------------------------------------------
// 2) Label Dictionaries for Display
// --------------------------------------------------
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

// --------------------------------------------------
// 3) Helper: Convert AccountType -> numeric ID
// --------------------------------------------------
function mapAccountToId(account?: AccountType): number {
  switch (account) {
    case "Bank":
      return 1;
    case "Wallet":
      return 2;
    case "Exchange":
      return 3;
    default:
      return 0;
  }
}

// --------------------------------------------------
// 4) Props for TransactionForm (For Panel Integration)
// --------------------------------------------------
interface TransactionFormProps {
  /**
   * Optional callback to inform the parent component whether
   * the form has unsaved changes (i.e., is "dirty").
   * We'll call it every time `formState.isDirty` changes.
   */
  onDirtyChange?: (dirty: boolean) => void;

  /**
   * Optional callback to signal the parent that
   * the form was successfully submitted (e.g., to close a panel).
   */
  onSubmitSuccess?: () => void;
}

// --------------------------------------------------
// 5) TransactionForm Component
// --------------------------------------------------
const TransactionForm: React.FC<TransactionFormProps> = ({
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
    },
  });

  const [currentType, setCurrentType] = useState<TransactionType | "">("");

  // Watch some fields for dynamic UI behavior
  const account = watch("account");
  const currency = watch("currency");
  const fromAccount = watch("fromAccount");

  // Notify parent if 'isDirty' changes
  useEffect(() => {
    if (onDirtyChange) {
      onDirtyChange(isDirty);
    }
  }, [isDirty, onDirtyChange]);

  // (A) Auto-set currency for deposit/withdrawal
  useEffect(() => {
    if (currentType === "Deposit" || currentType === "Withdrawal") {
      if (account === "Bank") {
        setValue("currency", "USD");
      } else if (account === "Wallet") {
        setValue("currency", "BTC");
      }
      // If account === "Exchange", user must choose
    }
  }, [account, currentType, setValue]);

  // For transfers, watch 'fromCurrency'
  const fromCurrencyVal = watch("fromCurrency");

  // 2) Auto-set fromCurrency/toCurrency for Transfers
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

  // (C) Reset form if user changes the transaction type
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

  // (D) Show cost basis if deposit + BTC
  const showCostBasisField =
    currentType === "Deposit" &&
    currency === "BTC" &&
    (account === "Wallet" || account === "Exchange");

  // (E) Submit Handler
  const onSubmit: SubmitHandler<TransactionFormData> = async (data) => {
    const isoTimestamp = new Date(data.timestamp).toISOString();
    let amountUSD = 0.0;
    let amountBTC = 0.0;
    let source = "N/A";
    let purpose = "N/A";
    let accountId = 0;

    switch (data.type) {
      case "Deposit":
        accountId = mapAccountToId(data.account);
        if (data.currency === "USD") {
          amountUSD = data.amount || 0;
        } else {
          amountBTC = data.amount || 0;
        }
        source = data.source || "N/A";
        break;

      case "Withdrawal":
        accountId = mapAccountToId(data.account);
        if (data.currency === "USD") {
          amountUSD = data.amount || 0;
        } else {
          amountBTC = data.amount || 0;
        }
        purpose = data.purpose || "N/A";
        break;

      case "Transfer":
        accountId = mapAccountToId(data.fromAccount);
        if (data.fromCurrency === "USD") {
          amountUSD = data.amountFrom || 0;
        } else {
          amountBTC = data.amountFrom || 0;
        }
        break;

      case "Buy":
        accountId = 3; // Exchange
        amountUSD = data.amountUSD || 0;
        amountBTC = data.amountBTC || 0;
        break;

      case "Sell":
        accountId = 3; // Exchange
        amountUSD = data.amountUSD || 0;
        amountBTC = data.amountBTC || 0;
        break;
    }

    // If depositing BTC, we might have a cost basis
    const finalCostBasis = showCostBasisField ? (data.costBasisUSD || 0) : 0;

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

    console.log("Submitting transaction to backend:", transactionPayload);

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/api/transactions",
        transactionPayload
      );
      console.log("Transaction created:", response.data);

      // Reset the form
      reset();
      setCurrentType("");

      alert("Transaction created successfully!");

      // If parent's callback is given, call it
      if (onSubmitSuccess) {
        onSubmitSuccess();
      }
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        console.error("Axios error creating transaction:", error.response?.data);
        const message =
          error.response?.data?.detail || error.message || "An error occurred";
        alert(`Failed to create transaction: ${message}`);
      } else if (error instanceof Error) {
        console.error("Error creating transaction:", error.message);
        alert(`Failed to create transaction: ${error.message}`);
      } else {
        console.error("Unexpected error creating transaction:", error);
        alert("An unexpected error occurred while creating the transaction.");
      }
    }
  };

  // (F) Render dynamic fields
  const renderDynamicFields = () => {
    switch (currentType) {
      case "Deposit":
        return (
          <>
            <div className="form-group">
              <label>Account:</label>
              <select className="form-control" {...register("account", { required: true })}>
                <option value="">Select Account</option>
                {Object.entries(accountLabels).map(([acctEnum, label]) => (
                  <option key={acctEnum} value={acctEnum}>
                    {label}
                  </option>
                ))}
              </select>
              {errors.account && <span className="error-text">Please select an account</span>}
            </div>
            <div className="form-group">
              <label>Currency:</label>
              {account === "Exchange" ? (
                <select className="form-control" {...register("currency", { required: true })}>
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
              {errors.currency && <span className="error-text">Currency is required</span>}
            </div>
            <div className="form-group">
              <label>Amount:</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("amount", { required: true, valueAsNumber: true })}
              />
              {errors.amount && <span className="error-text">Amount is required</span>}
            </div>
            <div className="form-group">
              <label>Source:</label>
              <select className="form-control" {...register("source", { required: true })}>
                <option value="N/A">N/A</option>
                <option value="My BTC">My BTC</option>
                <option value="Gift">Gift</option>
                <option value="Income">Income</option>
                <option value="Interest">Interest</option>
                <option value="Reward">Reward</option>
              </select>
              {errors.source && <span className="error-text">Source is required</span>}
            </div>
            <div className="form-group">
              <label>Fee (USD):</label>
              <input
                type="number"
                step="0.01"
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

      case "Withdrawal":
        return (
          <>
            <div className="form-group">
              <label>Account:</label>
              <select className="form-control" {...register("account", { required: true })}>
                <option value="">Select Account</option>
                {Object.entries(accountLabels).map(([acctEnum, label]) => (
                  <option key={acctEnum} value={acctEnum}>
                    {label}
                  </option>
                ))}
              </select>
              {errors.account && <span className="error-text">Please select an account</span>}
            </div>
            <div className="form-group">
              <label>Currency:</label>
              {account === "Exchange" ? (
                <select className="form-control" {...register("currency", { required: true })}>
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
              {errors.currency && <span className="error-text">Currency is required</span>}
            </div>
            <div className="form-group">
              <label>Amount:</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("amount", { required: true, valueAsNumber: true })}
              />
              {errors.amount && <span className="error-text">Amount is required</span>}
            </div>
            <div className="form-group">
              <label>Purpose:</label>
              <select className="form-control" {...register("purpose", { required: true })}>
                <option value="N/A">N/A</option>
                <option value="Spent">Spent</option>
                <option value="Gift">Gift</option>
                <option value="Donation">Donation</option>
                <option value="Lost">Lost</option>
              </select>
              {errors.purpose && <span className="error-text">Purpose is required</span>}
            </div>
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
            <div className="form-group">
              <label>From Account:</label>
              <select className="form-control" {...register("fromAccount", { required: true })}>
                <option value="">Select From Account</option>
                {Object.entries(accountLabels).map(([acctEnum, label]) => (
                  <option key={acctEnum} value={acctEnum}>
                    {label}
                  </option>
                ))}
              </select>
              {errors.fromAccount && (
                <span className="error-text">From Account is required</span>
              )}
            </div>
            <div className="form-group">
              <label>From Currency:</label>
              {fromAccount === "Exchange" ? (
                <select className="form-control" {...register("fromCurrency", { required: true })}>
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
                {...register("amountFrom", { required: true, valueAsNumber: true })}
              />
              {errors.amountFrom && (
                <span className="error-text">Amount (From) is required</span>
              )}
            </div>

            {/* We auto-populate the toAccount/toCurrency, just for display */}
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
                {...register("amountTo", { required: true, valueAsNumber: true })}
              />
              {errors.amountTo && (
                <span className="error-text">Amount (To) is required</span>
              )}
            </div>
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
                {...register("amountUSD", { required: true, valueAsNumber: true })}
              />
              {errors.amountUSD && <span className="error-text">Amount USD is required</span>}
            </div>
            <div className="form-group">
              <label>Amount BTC:</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("amountBTC", { required: true, valueAsNumber: true })}
              />
              {errors.amountBTC && <span className="error-text">Amount BTC is required</span>}
            </div>
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
                {...register("amountBTC", { required: true, valueAsNumber: true })}
              />
              {errors.amountBTC && <span className="error-text">Amount BTC is required</span>}
            </div>
            <div className="form-group">
              <label>Amount USD:</label>
              <input
                type="number"
                step="0.01"
                className="form-control"
                {...register("amountUSD", { required: true, valueAsNumber: true })}
              />
              {errors.amountUSD && <span className="error-text">Amount USD is required</span>}
            </div>
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
        return null;
    }
  };

  // (G) Final Rendering: now we put the dynamic fields inside .form-fields-grid
  return (
    <form className="transaction-form" onSubmit={handleSubmit(onSubmit)}>
      {/* Basic fields above the grid */}
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

      {/* Put all dynamic form fields in a grid wrapper */}
      <div className="form-fields-grid">
        {renderDynamicFields()}
      </div>

      {/* Optionally keep or remove this 'Submit' if your panel has "Save" */}
      <button type="submit" className="submit-button">
        Submit Transaction
      </button>
    </form>
  );
};

export default TransactionForm;