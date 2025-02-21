import React, { useState, useEffect } from "react";
import { useForm, SubmitHandler } from "react-hook-form";
import axios from "axios";
import "../styles/transactionForm.css";

/**
 * -----------
 * 1) Types
 * -----------
 * Keeping them the same, but we'll add a new field "feeInUsdDisplay"
 * in the component state for optional display of the BTC fee in USD.
 */

type TransactionType = "Deposit" | "Withdrawal" | "Transfer" | "Buy" | "Sell";
type AccountType = "Bank" | "Wallet" | "Exchange";
type DepositSource = "N/A" | "MyBTC" | "Gift" | "Income" | "Interest" | "Reward";
type WithdrawalPurpose = "N/A" | "Spent" | "Gift" | "Donation" | "Lost";
type Currency = "USD" | "BTC";

interface TransactionFormData {
  type: TransactionType;
  timestamp: string;

  // Single-account transactions
  account?: AccountType;
  currency?: Currency;
  amount?: number;
  source?: DepositSource;     // BTC deposit
  purpose?: WithdrawalPurpose; // BTC withdrawal
  fee?: number;               // the numeric fee, which might be BTC or USD
  costBasisUSD?: number;

  // Transfer
  fromAccount?: AccountType;
  fromCurrency?: Currency;
  toAccount?: AccountType;
  toCurrency?: Currency;
  amountFrom?: number;  // BTC or USD
  amountTo?: number;    // BTC or USD

  // Buy/Sell
  amountUSD?: number;
  amountBTC?: number;
}

/** Hardcoded account -> ID mappings */
const EXTERNAL_ID = 99; // "External"
const EXCHANGE_USD_ID = 3;
const EXCHANGE_BTC_ID = 4;

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

interface TransactionFormProps {
  id?: string;
  onDirtyChange?: (dirty: boolean) => void;
  onSubmitSuccess?: () => void;
}

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

  // A local state to store the type, to reset form on changes
  const [currentType, setCurrentType] = useState<TransactionType | "">("");

  // We'll store a local state for optional "feeInUsdDisplay" so we can show
  // an approximate USD cost for the BTC fee. In real code, we'd fetch from an API.
  const [feeInUsdDisplay, setFeeInUsdDisplay] = useState<number>(0);

  /** 
   * Watches for dynamic fields relevant to "Transfer" 
   * We'll recalc fee = amountFrom - amountTo for BTC transfers.
   */
  const amountFromVal = watch("amountFrom") || 0;
  const amountToVal = watch("amountTo") || 0;
  const fromCurrencyVal = watch("fromCurrency"); // could be BTC or USD

  // For deposit/withdrawal logic
  const account = watch("account");
  const currency = watch("currency");

  // For buy/sell
  const amountUsdVal = watch("amountUSD") || 0;
  const amountBtcVal = watch("amountBTC") || 0;

  useEffect(() => {
    console.log("User typed in amountUSD:", amountUsdVal);
  }, [amountUsdVal]);

  useEffect(() => {
    console.log("User typed in amountBTC:", amountBtcVal);
  }, [amountBtcVal]);  

  // track dirty state in parent
  useEffect(() => {
    onDirtyChange?.(isDirty);
  }, [isDirty, onDirtyChange]);

  /**
   * If user chooses Deposit or Withdrawal, auto-set currency based on account
   */
  useEffect(() => {
    if (currentType === "Deposit" || currentType === "Withdrawal") {
      if (account === "Bank") {
        setValue("currency", "USD");
      } else if (account === "Wallet") {
        setValue("currency", "BTC");
      }
    }
    // if Exchange, user picks
  }, [account, currentType, setValue]);

  /**
   * Transfer logic: fromAccount => toAccount
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
   * If user changes transaction type, reset form except for the type and timestamp
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
   * Show costBasis only if deposit => BTC => wallet or exchange
   */
  const showCostBasisField =
    currentType === "Deposit" &&
    currency === "BTC" &&
    (account === "Wallet" || account === "Exchange");

  /**
   * Auto-calculate fee for BTC Transfers, read-only
   * If negative, clamp to 0 & optionally show an error
   */
  useEffect(() => {
    if (currentType === "Transfer") {
      // only do this for BTC transfers
      if (fromCurrencyVal !== "BTC") {
        // If from is not BTC, we won't auto-calc fee. 
        // Possibly the user does a USD transfer? You can adapt as needed.
        return;
      }
      const calcFee = amountFromVal - amountToVal;
      if (calcFee < 0) {
        // clamp to 0
        setValue("fee", 0);
      } else {
        // round to 8 decimals
        const feeBtc = Number(calcFee.toFixed(8));
        setValue("fee", feeBtc);

        // If we want to show ~USD, we do a mock conversion for now (e.g. 1 BTC = $30k)
        // In real code, fetch from an API with the transaction timestamp.
        const btcPrice = 30000; // mock
        const approxUsd = feeBtc * btcPrice;
        setFeeInUsdDisplay(Number(approxUsd.toFixed(2)));
      }
    }
  }, [currentType, fromCurrencyVal, amountFromVal, amountToVal, setValue]);

  /**
   * onSubmit => build final payload
   */
  const onSubmit: SubmitHandler<TransactionFormData> = async (data) => {
    const { from_account_id, to_account_id } = mapDoubleEntryAccounts(data);
    const isoTimestamp = new Date(data.timestamp).toISOString();

    let amount = 0;
    let feeCurrency = "USD"; // fallback
    let source: string | undefined = undefined;
    let purpose: string | undefined = undefined;
    let cost_basis_usd = 0;
    let proceeds_usd = undefined;

    switch (data.type) {
      case "Deposit": {
        amount = data.amount || 0;
        feeCurrency = data.currency === "BTC" ? "BTC" : "USD";
        source = data.source && data.source !== "N/A" ? data.source : "N/A";
        if (showCostBasisField) {
          cost_basis_usd = data.costBasisUSD || 0;
        }
        break;
      }
      case "Withdrawal": {
        amount = data.amount || 0;
        feeCurrency = data.currency === "BTC" ? "BTC" : "USD";
        purpose = data.purpose && data.purpose !== "N/A" ? data.purpose : "N/A";
        break;
      }
      case "Transfer": {
        amount = data.amountFrom || 0; // from side
        // we assume it's BTC if fromCurrency is BTC
        if (data.fromCurrency === "BTC") feeCurrency = "BTC";
        else feeCurrency = "USD"; // or do some logic
        break;
      }
      case "Buy": {
        amount = data.amountUSD || 0;
        feeCurrency = "USD";
        cost_basis_usd = amount;
        break;
      }
      case "Sell": {
        amount = data.amountBTC || 0;
        feeCurrency = "USD";
        proceeds_usd = data.amountUSD || 0;
        break;
      }
    }

    const transactionPayload = {
      from_account_id,
      to_account_id,
      type: data.type,
      amount,
      timestamp: isoTimestamp,
      fee_amount: data.fee || 0,
      fee_currency: feeCurrency,
      cost_basis_usd,
      proceeds_usd,
      source,
      purpose,
      is_locked: false,
    };

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/api/transactions",
        transactionPayload
      );
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
   * Renders dynamic fields based on transaction type
   */
  const renderDynamicFields = () => {
    switch (currentType) {
      case "Deposit":
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

            <div className="form-group">
              <label>Source (BTC only):</label>
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
        // The main place we do auto-fee in BTC
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
              {/* If fromAccount=Exchange => user picks BTC or USD */}
              <input
                type="text"
                className="form-control"
                {...register("fromCurrency")}
                readOnly={fromAccount !== "Exchange"}
              />
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
              <label>Fee (BTC):</label>
              <input
                type="number"
                step="0.00000001"
                className="form-control"
                {...register("fee", { valueAsNumber: true })}
                readOnly
              />
              {/* Optional label to show approximate USD */}
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

        {/* Render dynamic fields */}
        {renderDynamicFields()}
      </div>
    </form>
  );
};

export default TransactionForm;
