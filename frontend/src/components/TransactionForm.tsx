import React, { useState, useEffect } from "react";
import { useForm, SubmitHandler } from "react-hook-form";
import axios from "axios";
import "../styles/transactionForm.css";

/**
 * -----------------------------------------------------------
 * 1) Enumerations & Types
 * -----------------------------------------------------------
 */
type TransactionType = "Deposit" | "Withdrawal" | "Transfer" | "Buy" | "Sell";
type AccountType = "Bank" | "Wallet" | "Exchange";
type DepositSource = "N/A" | "My BTC" | "Gift" | "Income" | "Interest" | "Reward";
type WithdrawalPurpose = "N/A" | "Spent" | "Gift" | "Donation" | "Lost";
type Currency = "USD" | "BTC";

/**
 * The form data shape from react-hook-form
 */
interface TransactionFormData {
  // Basic
  type: TransactionType;
  timestamp: string;
  account?: AccountType;       
  currency?: Currency;
  amount?: number;             
  source?: DepositSource;      
  purpose?: WithdrawalPurpose; 
  fee?: number;
  costBasisUSD?: number;       

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
 * -----------------------------------------------------------
 * 2) Label dictionaries (unchanged)
 * -----------------------------------------------------------
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
 * -----------------------------------------------------------
 * 3) ID Mappings for Double-Entry
 * -----------------------------------------------------------
 * We have: 
 *   Bank = 1, 
 *   Wallet = 2, 
 *   ExchangeUSD = 3, 
 *   ExchangeBTC = 4, 
 *   External = 99
 */

/** 
 * We’ll map “Bank” => 1, “Wallet” => 2, 
 * “Exchange” => 3 or 4, depending on currency.
 * If no currency is provided (edge case), default to ExchangeUSD=3.
 */
function mapAccountToId(account?: AccountType, currency?: Currency): number {
  if (account === "Bank") return 1;
  if (account === "Wallet") return 2;
  if (account === "Exchange") {
    if (currency === "BTC") return 4;  // ExchangeBTC
    return 3;                         // ExchangeUSD by default
  }
  return 0; // fallback
}

const EXTERNAL_ID = 99; // "External"  
const EXCHANGE_USD_ID = 3;
const EXCHANGE_BTC_ID = 4;

/** 
 * mapDoubleEntryAccounts: determines from_account_id / to_account_id
 * based on transaction type and (optionally) currency.
 */
function mapDoubleEntryAccounts(data: TransactionFormData): {
  from_account_id: number;
  to_account_id: number;
} {
  switch (data.type) {
    case "Deposit": {
      // from= EXTERNAL, to= chosen "account" + currency
      return {
        from_account_id: EXTERNAL_ID,
        to_account_id: mapAccountToId(data.account, data.currency),
      };
    }
    case "Withdrawal": {
      // from= chosen "account" + currency, to= EXTERNAL
      return {
        from_account_id: mapAccountToId(data.account, data.currency),
        to_account_id: EXTERNAL_ID,
      };
    }
    case "Transfer": {
      // from= fromAccount/fromCurrency, to= toAccount/toCurrency
      return {
        from_account_id: mapAccountToId(data.fromAccount, data.fromCurrency),
        to_account_id: mapAccountToId(data.toAccount, data.toCurrency),
      };
    }
    case "Buy": {
      // from= ExchangeUSD=3 => to= ExchangeBTC=4
      return {
        from_account_id: EXCHANGE_USD_ID,
        to_account_id: EXCHANGE_BTC_ID,
      };
    }
    case "Sell": {
      // from= ExchangeBTC=4 => to= ExchangeUSD=3
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
 * 4) Props
 * -----------------------------------------------------------
 */
interface TransactionFormProps {
  id?: string;
  onDirtyChange?: (dirty: boolean) => void;
  onSubmitSuccess?: () => void;
}

/**
 * -----------------------------------------------------------
 * 5) TransactionForm
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
      // if "Exchange", user picks manually => do nothing
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

    // Keep or reset the fields we want
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
   * onSubmit -> build new double-entry payload
   * -----------------------------------------------------------
   */
  const onSubmit: SubmitHandler<TransactionFormData> = async (data) => {
    const isoTimestamp = new Date(data.timestamp).toISOString();

    // 1) Determine from_account_id / to_account_id with new function
    const { from_account_id, to_account_id } = mapDoubleEntryAccounts(data);

    // 2) Decide amounts in USD vs BTC
    let amountUSD = 0.0;
    let amountBTC = 0.0;
    let source = "N/A";
    let purpose = "N/A";

    switch (data.type) {
      case "Deposit": {
        if (data.currency === "USD") {
          amountUSD = data.amount || 0;
        } else {
          amountBTC = data.amount || 0;
        }
        source = data.source || "N/A";
        break;
      }
      case "Withdrawal": {
        if (data.currency === "USD") {
          amountUSD = data.amount || 0;
        } else {
          amountBTC = data.amount || 0;
        }
        purpose = data.purpose || "N/A";
        break;
      }
      case "Transfer": {
        // "From" side: set amounts for the currency from fromCurrency
        if (data.fromCurrency === "USD") {
          amountUSD = data.amountFrom || 0;
        } else {
          amountBTC = data.amountFrom || 0;
        }
        // (We ignore data.amountTo here; fee is separate)
        break;
      }
      case "Buy": {
        // from=3 (USD), to=4 (BTC)
        amountUSD = data.amountUSD || 0;
        amountBTC = data.amountBTC || 0;
        break;
      }
      case "Sell": {
        // from=4 (BTC), to=3 (USD)
        amountBTC = data.amountBTC || 0;
        amountUSD = data.amountUSD || 0;
        break;
      }
      default:
        break;
    }

    // 3) If it's a BTC deposit with a cost basis
    const finalCostBasis = showCostBasisField ? (data.costBasisUSD || 0) : 0;

    // 4) Build the payload
    const transactionPayload = {
      from_account_id,
      to_account_id,
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

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/api/transactions",
        transactionPayload
      );
      console.log("Transaction created:", response.data);

      // Reset form + notify
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
   * Dynamic Fields (same UI as original)
   * -----------------------------------------------------------
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

            {/* To Account (auto-filled) */}
            <div className="form-group">
              <label>To Account:</label>
              <input
                type="text"
                className="form-control"
                {...register("toAccount")}
                readOnly
              />
            </div>

            {/* To Currency (auto-filled) */}
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

      case "Buy":
        return (
          <>
            {/* Account always Exchange (in UI) */}
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
                {...register("amountBTC", { required: true, valueAsNumber: true })}
              />
              {errors.amountBTC && (
                <span className="error-text">Amount BTC is required</span>
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

      case "Sell":
        return (
          <>
            {/* Account always Exchange (in UI) */}
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
                {...register("amountUSD", { required: true, valueAsNumber: true })}
              />
              {errors.amountUSD && (
                <span className="error-text">Amount USD is required</span>
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

      default:
        return null;
    }
  };

  /**
   * 6) Render
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

        {/* The rest of the fields are dynamically rendered */}
        {renderDynamicFields()}
      </div>
    </form>
  );
};

export default TransactionForm;
