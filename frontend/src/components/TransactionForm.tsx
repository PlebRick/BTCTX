import React, { useState, useEffect } from "react";
import { useForm, SubmitHandler } from "react-hook-form";
import axios from "axios";
import "../styles/transactionForm.css";

/**
 * -----------------------------------------------------------
 * 1) Enumerations & Types for Frontend
 * -----------------------------------------------------------
 * We'll keep your existing type definitions for user-friendly UI,
 * but note that the backend now expects a single `amount` plus optional
 * `source`, `purpose`, `fee_amount`, `fee_currency`, etc.
 */
type TransactionType = "Deposit" | "Withdrawal" | "Transfer" | "Buy" | "Sell";
type AccountType = "Bank" | "Wallet" | "Exchange";
type DepositSource = "N/A" | "My BTC" | "Gift" | "Income" | "Interest" | "Reward";
type WithdrawalPurpose = "N/A" | "Spent" | "Gift" | "Donation" | "Lost";
type Currency = "USD" | "BTC";

/**
 * The form data shape from react-hook-form.
 * We'll keep it largely the same so that the UI remains familiar.
 */
interface TransactionFormData {
  type: TransactionType;
  timestamp: string;

  // Single-account transactions
  account?: AccountType;
  currency?: Currency;
  amount?: number;
  source?: DepositSource;     // BTC deposit
  purpose?: WithdrawalPurpose; // BTC withdrawal
  fee?: number;               // we will map this to fee_amount, and pick fee_currency
  costBasisUSD?: number;      // for external BTC deposit or "Buy"

  // Transfer
  fromAccount?: AccountType;
  fromCurrency?: Currency;
  toAccount?: AccountType;
  toCurrency?: Currency;
  amountFrom?: number;
  amountTo?: number;  // not used in the backend, but still displayed in UI

  // Buy/Sell
  amountUSD?: number;
  amountBTC?: number;
}

/**
 * -----------------------------------------------------------
 * 2) Mappings for Double-Entry
 * -----------------------------------------------------------
 */
const EXTERNAL_ID = 99; // "External"
const EXCHANGE_USD_ID = 3;
const EXCHANGE_BTC_ID = 4;

/**
 * mapAccountToId: Updated to your known IDs.
 * In a real app, you'd fetch these from the backend. Hardcoded for example.
 */
function mapAccountToId(account?: AccountType, currency?: Currency): number {
  if (account === "Bank") return 1;
  if (account === "Wallet") return 2;
  // "Exchange" => decide by currency
  if (account === "Exchange") {
    if (currency === "BTC") return EXCHANGE_BTC_ID;
    return EXCHANGE_USD_ID;
  }
  return 0;
}

/**
 * mapDoubleEntryAccounts: same logic as before, with from_account_id & to_account_id
 */
function mapDoubleEntryAccounts(data: TransactionFormData): {
  from_account_id: number;
  to_account_id: number;
} {
  switch (data.type) {
    case "Deposit": {
      // from= external, to= user-chosen
      return {
        from_account_id: EXTERNAL_ID,
        to_account_id: mapAccountToId(data.account, data.currency),
      };
    }
    case "Withdrawal": {
      // from= user-chosen, to= external
      return {
        from_account_id: mapAccountToId(data.account, data.currency),
        to_account_id: EXTERNAL_ID,
      };
    }
    case "Transfer": {
      return {
        from_account_id: mapAccountToId(data.fromAccount, data.fromCurrency),
        to_account_id: mapAccountToId(data.toAccount, data.toCurrency),
      };
    }
    case "Buy": {
      // from= ExchangeUSD => to= ExchangeBTC
      return {
        from_account_id: EXCHANGE_USD_ID,
        to_account_id: EXCHANGE_BTC_ID,
      };
    }
    case "Sell": {
      // from= ExchangeBTC => to= ExchangeUSD
      return {
        from_account_id: EXCHANGE_BTC_ID,
        to_account_id: EXCHANGE_USD_ID,
      };
    }
    default:
      return { from_account_id: 0, to_account_id: 0 };
  }
}

/**
 * -----------------------------------------------------------
 * 3) Props
 * -----------------------------------------------------------
 */
interface TransactionFormProps {
  id?: string;
  onDirtyChange?: (dirty: boolean) => void;
  onSubmitSuccess?: () => void;
}

/**
 * -----------------------------------------------------------
 * 4) TransactionForm
 * -----------------------------------------------------------
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
    },
  });

  // Basic states to handle dynamic form
  const [currentType, setCurrentType] = useState<TransactionType | "">("");
  const account = watch("account");
  const currency = watch("currency");
  const fromAccount = watch("fromAccount");
  const fromCurrencyVal = watch("fromCurrency");

  // Track dirty state in parent
  useEffect(() => {
    onDirtyChange?.(isDirty);
  }, [isDirty, onDirtyChange]);

  // Auto-set currency for deposit/withdrawal
  useEffect(() => {
    if (currentType === "Deposit" || currentType === "Withdrawal") {
      if (account === "Bank") {
        setValue("currency", "USD");
      } else if (account === "Wallet") {
        setValue("currency", "BTC");
      }
      // if "Exchange", user picks manually
    }
  }, [account, currentType, setValue]);

  // Auto-set from/to for Transfer
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

  // Reset form on type change
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

  // Show costBasis if depositing BTC into wallet/exchange
  const showCostBasisField =
    currentType === "Deposit" &&
    currency === "BTC" &&
    (account === "Wallet" || account === "Exchange");

  /**
   * -----------------------------------------------------------
   * onSubmit => Build payload to match new backend
   * -----------------------------------------------------------
   */
  const onSubmit: SubmitHandler<TransactionFormData> = async (data) => {
    // 1) from/to IDs
    const { from_account_id, to_account_id } = mapDoubleEntryAccounts(data);
    const isoTimestamp = new Date(data.timestamp).toISOString();

    // 2) Derive a single "amount" from user inputs
    let amount = 0; // The main transaction amount
    let feeCurrency = "USD"; // default if we want the user to pick or guess
    let source: string | undefined = undefined;
    let purpose: string | undefined = undefined;
    let cost_basis_usd = 0;
    let proceeds_usd = undefined; // for sells

    switch (data.type) {
      case "Deposit": {
        // amount = data.amount
        amount = data.amount || 0;
        // If deposit is BTC => feeCurrency = "BTC"
        feeCurrency = data.currency === "BTC" ? "BTC" : "USD";

        // `source` might come from data.source
        // The backend expects an enum string, e.g. "Gift", "Income", etc.
        // If user left it "N/A", we can pass "N/A".
        source = data.source && data.source !== "N/A" ? data.source : "N/A";

        // If it's a BTC deposit, user can set costBasisUSD
        if (showCostBasisField) {
          cost_basis_usd = data.costBasisUSD || 0;
        }
        break;
      }
      case "Withdrawal": {
        amount = data.amount || 0;
        feeCurrency = data.currency === "BTC" ? "BTC" : "USD";

        // `purpose` might come from data.purpose
        purpose = data.purpose && data.purpose !== "N/A" ? data.purpose : "N/A";
        break;
      }
      case "Transfer": {
        amount = data.amountFrom || 0; // from side
        // If the user picks fromCurrency = BTC, fee is in BTC
        feeCurrency = data.fromCurrency === "BTC" ? "BTC" : "USD";
        // We don't have source/purpose for transfers
        break;
      }
      case "Buy": {
        // from= ExchangeUSD => amount in USD
        amount = data.amountUSD || 0;
        feeCurrency = "USD";

        // For a buy, we can set cost_basis_usd
        cost_basis_usd = amount;
        break;
      }
      case "Sell": {
        // from= ExchangeBTC => amount in BTC
        amount = data.amountBTC || 0;
        // We assume fee in USD or BTC; the UI says "Fee (USD)" so let's keep it "USD"
        feeCurrency = "USD";

        // For a sell, we can set proceeds_usd
        proceeds_usd = data.amountUSD || 0;
        break;
      }
    }

    // 3) Build final payload for new backend
    const transactionPayload = {
      from_account_id,
      to_account_id,
      type: data.type,
      amount,                // single decimal
      timestamp: isoTimestamp,
      fee_amount: data.fee || 0,
      fee_currency: feeCurrency,
      cost_basis_usd,
      proceeds_usd,

      // `source` & `purpose` for deposit/withdrawal (enums in backend)
      source,   // e.g. "Gift", "Income"
      purpose,  // e.g. "Spent", "Donation"

      // We set lock to false by default
      is_locked: false,
    };

    try {
      const response = await axios.post("http://127.0.0.1:8000/api/transactions", transactionPayload);
      console.log("Transaction created:", response.data);

      // Reset form
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
   * 5) Dynamic Fields - same UI but with "source" & "purpose"
   * -----------------------------------------------------------
   * We'll keep your existing structure, just clarifying these fields
   * get mapped into the final payload's `source` and `purpose`.
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
                <option value="Bank">Bank Account</option>
                <option value="Wallet">Bitcoin Wallet</option>
                <option value="Exchange">Exchange</option>
              </select>
              {errors.account && <span className="error-text">Please select an account</span>}
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
              {errors.currency && <span className="error-text">Currency is required</span>}
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
              {errors.amount && <span className="error-text">Amount is required</span>}
            </div>

            {/* Source (only relevant if BTC, but we'll keep it for all) */}
            <div className="form-group">
              <label>Source (BTC only):</label>
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
            </div>

            {/* Fee (USD) for now (though we do handle BTC logic in the final payload) */}
            <div className="form-group">
              <label>Fee:</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("fee", { valueAsNumber: true })}
              />
            </div>

            {/* Optional Cost Basis if BTC deposit */}
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
              <select
                className="form-control"
                {...register("account", { required: true })}
              >
                <option value="">Select Account</option>
                <option value="Bank">Bank Account</option>
                <option value="Wallet">Bitcoin Wallet</option>
                <option value="Exchange">Exchange</option>
              </select>
              {errors.account && <span className="error-text">Please select an account</span>}
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

            {/* Purpose (BTC only) */}
            <div className="form-group">
              <label>Purpose (BTC only):</label>
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
            </div>

            <div className="form-group">
              <label>Fee:</label>
              <input
                type="number"
                step="0.00000001"
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
              <select
                className="form-control"
                {...register("fromAccount", { required: true })}
              >
                <option value="">Select From Account</option>
                <option value="Bank">Bank Account</option>
                <option value="Wallet">Bitcoin Wallet</option>
                <option value="Exchange">Exchange</option>
              </select>
              {errors.fromAccount && <span className="error-text">From Account is required</span>}
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
              {errors.fromCurrency && <span className="error-text">From Currency is required</span>}
            </div>

            <div className="form-group">
              <label>Amount (From):</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("amountFrom", { required: true, valueAsNumber: true })}
              />
              {errors.amountFrom && <span className="error-text">Amount (From) is required</span>}
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
                {...register("amountTo", { required: true, valueAsNumber: true })}
              />
              {errors.amountTo && <span className="error-text">Amount (To) is required</span>}
            </div>

            <div className="form-group">
              <label>Fee:</label>
              <input
                type="number"
                step="0.00000001"
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
              <label>Fee:</label>
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
              <label>Fee:</label>
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

  /**
   * -----------------------------------------------------------
   * 6) Render
   * -----------------------------------------------------------
   */
  return (
    <form
      id={id || "transactionFormId"}
      className="transaction-form"
      onSubmit={handleSubmit(onSubmit)}
    >
      <div className="form-fields-grid">
        {/* Transaction Type + timestamp */}
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

        {/* Dynamic fields */}
        {renderDynamicFields()}
      </div>
    </form>
  );
};

export default TransactionForm;
