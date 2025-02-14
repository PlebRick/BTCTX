import React, { useState, useEffect } from "react";
import { useForm, SubmitHandler } from "react-hook-form";
import axios from "axios";

// --------------------------------------------------
// 1) TypeScript Types & Enums (Matching the Backend)
// --------------------------------------------------
type TransactionType = "Deposit" | "Withdrawal" | "Transfer" | "Buy" | "Sell";

type AccountType = "Bank" | "Wallet" | "Exchange";

// The backend's TransactionSource enum has these values:
type DepositSource = "N/A" | "My BTC" | "Gift" | "Income" | "Interest" | "Reward";

// The backend's TransactionPurpose enum:
type WithdrawalPurpose = "N/A" | "Spent" | "Gift" | "Donation" | "Lost";

type Currency = "USD" | "BTC";

// The shape of the form data we'll capture before sending to the backend
interface TransactionFormData {
  // Basic
  type: TransactionType;
  timestamp: string;        // We'll convert to ISO string for the backend

  // Single-Account transactions (Deposit, Withdrawal, Buy, Sell)
  account?: AccountType;
  currency?: Currency;
  amount?: number;
  source?: DepositSource;   // Only used if type = "Deposit"
  purpose?: WithdrawalPurpose; // Only used if type = "Withdrawal"
  fee?: number;             // Always in USD

  // Cost Basis for a BTC deposit
  costBasisUSD?: number;

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
// 2) Label Dictionaries (Optional User-Friendly Text)
// --------------------------------------------------

// Here, we keep the actual keys the same as the backend, 
// but you can change the displayed labels if you want.
const transactionTypeLabels: Record<TransactionType, string> = {
  Deposit: "Deposit",
  Withdrawal: "Withdrawal",
  Transfer: "Transfer",
  Buy: "Buy",
  Sell: "Sell",
};

// If you want to do the same for accounts or any other field, you can.
const accountLabels: Record<AccountType, string> = {
  Bank: "Bank Account",
  Wallet: "Bitcoin Wallet",
  Exchange: "Exchange",
};

// --------------------------------------------------
// 3) Helpers: Converting AccountType -> numeric ID
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
      return 0; // or throw an error
  }
}

// --------------------------------------------------
// 4) The Form Component
// --------------------------------------------------
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
      // By default, set the timestamp to "now" for a datetime-local input
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
  const toAccount = watch("toAccount");

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

  // (B) Auto-set fromCurrency/toCurrency for transfers
  useEffect(() => {
    if (currentType === "Transfer") {
      if (fromAccount === "Bank") {
        setValue("fromCurrency", "USD");
        setValue("toAccount", "Exchange");
        setValue("toCurrency", "USD");
      } else if (fromAccount === "Wallet") {
        setValue("fromCurrency", "BTC");
        setValue("toAccount", "Exchange");
        setValue("toCurrency", "BTC");
      } else if (fromAccount === "Exchange") {
        const selectedCurrency = watch("fromCurrency");
        if (selectedCurrency === "USD") {
          setValue("toAccount", "Bank");
          setValue("toCurrency", "USD");
        } else if (selectedCurrency === "BTC") {
          setValue("toAccount", "Wallet");
          setValue("toCurrency", "BTC");
        }
      }
    }
  }, [fromAccount, toAccount, currentType, setValue, watch]);

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

  // (E) Submit Handler: build the final payload for the backend
  const onSubmit: SubmitHandler<TransactionFormData> = async (data) => {
    // Convert the local datetime to an ISO string
    const isoTimestamp = new Date(data.timestamp).toISOString();

    // Default values
    let amountUSD = 0.0;
    let amountBTC = 0.0;
    let source: string = "N/A";
    let purpose: string = "N/A";
    let accountId = 0;

    // The 'type' here already matches the backend exactly 
    // (e.g. "Deposit", "Withdrawal", etc.).
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
        // Single-record transfer is incomplete in the DB. We only store 'from' side.
        accountId = mapAccountToId(data.fromAccount);
        if (data.fromCurrency === "USD") {
          amountUSD = data.amountFrom || 0;
        } else {
          amountBTC = data.amountFrom || 0;
        }
        // The "to" side is just UI-only for now
        break;

      case "Buy":
        accountId = 3; // Exchange ID
        amountUSD = data.amountUSD || 0;
        amountBTC = data.amountBTC || 0;
        break;

      case "Sell":
        accountId = 3; // Exchange ID
        amountUSD = data.amountUSD || 0;
        amountBTC = data.amountBTC || 0;
        break;
    }

    // If we're depositing BTC, we might have a cost basis
    const finalCostBasis = showCostBasisField ? (data.costBasisUSD || 0) : 0;

    // Build the final payload for the backend
    const transactionPayload = {
      account_id: accountId,
      type: data.type,           // e.g. "Deposit"
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
      // Adjust the URL as needed; add auth headers if required.
      const response = await axios.post(
        "http://127.0.0.1:8000/api/transactions",
        transactionPayload
      );
      console.log("Transaction created:", response.data);

      // Reset form or set success message
      reset();
      setCurrentType("");
      alert("Transaction created successfully!");
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        // Error is specifically an AxiosError
        console.error("Axios error creating transaction:", error.response?.data);
        const message = error.response?.data?.detail || error.message || "An error occurred";
        alert(`Failed to create transaction: ${message}`);
      } else if (error instanceof Error) {
        // Error is a generic JS Error
        console.error("Error creating transaction:", error.message);
        alert(`Failed to create transaction: ${error.message}`);
      } else {
        // Fallback for anything else (non-Error objects, etc.)
        console.error("Unexpected error creating transaction:", error);
        alert("An unexpected error occurred while creating the transaction.");
      }
    }
  };

  // (F) Render dynamic fields for each transaction type
  const renderDynamicFields = () => {
    switch (currentType) {
      case "Deposit":
        return (
          <>
            <div>
              <label>Account:</label>
              <select {...register("account", { required: true })}>
                <option value="">Select Account</option>
                {Object.entries(accountLabels).map(([acctEnum, label]) => (
                  <option key={acctEnum} value={acctEnum}>
                    {label}
                  </option>
                ))}
              </select>
              {errors.account && <span>Please select an account</span>}
            </div>
            <div>
              <label>Currency:</label>
              {account === "Exchange" ? (
                <select {...register("currency", { required: true })}>
                  <option value="">Select Currency</option>
                  <option value="USD">USD</option>
                  <option value="BTC">BTC</option>
                </select>
              ) : (
                <input type="text" {...register("currency")} readOnly />
              )}
              {errors.currency && <span>Currency is required</span>}
            </div>
            <div>
              <label>Amount:</label>
              <input
                type="number"
                step="0.00000001"
                {...register("amount", { required: true, valueAsNumber: true })}
              />
              {errors.amount && <span>Amount is required</span>}
            </div>
            <div>
              <label>Source:</label>
              <select {...register("source", { required: true })}>
                <option value="N/A">N/A</option>
                <option value="My BTC">My BTC</option>
                <option value="Gift">Gift</option>
                <option value="Income">Income</option>
                <option value="Interest">Interest</option>
                <option value="Reward">Reward</option>
              </select>
              {errors.source && <span>Source is required</span>}
            </div>
            <div>
              <label>Fee (USD):</label>
              <input type="number" step="0.01" {...register("fee", { valueAsNumber: true })} />
            </div>
            {showCostBasisField && (
              <div>
                <label>Cost Basis (USD):</label>
                <input
                  type="number"
                  step="0.01"
                  {...register("costBasisUSD", { valueAsNumber: true })}
                />
              </div>
            )}
          </>
        );

      case "Withdrawal":
        return (
          <>
            <div>
              <label>Account:</label>
              <select {...register("account", { required: true })}>
                <option value="">Select Account</option>
                {Object.entries(accountLabels).map(([acctEnum, label]) => (
                  <option key={acctEnum} value={acctEnum}>
                    {label}
                  </option>
                ))}
              </select>
              {errors.account && <span>Please select an account</span>}
            </div>
            <div>
              <label>Currency:</label>
              {account === "Exchange" ? (
                <select {...register("currency", { required: true })}>
                  <option value="">Select Currency</option>
                  <option value="USD">USD</option>
                  <option value="BTC">BTC</option>
                </select>
              ) : (
                <input type="text" {...register("currency")} readOnly />
              )}
              {errors.currency && <span>Currency is required</span>}
            </div>
            <div>
              <label>Amount:</label>
              <input
                type="number"
                step="0.00000001"
                {...register("amount", { required: true, valueAsNumber: true })}
              />
              {errors.amount && <span>Amount is required</span>}
            </div>
            <div>
              <label>Purpose:</label>
              <select {...register("purpose", { required: true })}>
                <option value="N/A">N/A</option>
                <option value="Spent">Spent</option>
                <option value="Gift">Gift</option>
                <option value="Donation">Donation</option>
                <option value="Lost">Lost</option>
              </select>
              {errors.purpose && <span>Purpose is required</span>}
            </div>
            <div>
              <label>Fee (USD):</label>
              <input type="number" step="0.01" {...register("fee", { valueAsNumber: true })} />
            </div>
          </>
        );

      case "Transfer":
        return (
          <>
            <div>
              <label>From Account:</label>
              <select {...register("fromAccount", { required: true })}>
                <option value="">Select From Account</option>
                {Object.entries(accountLabels).map(([acctEnum, label]) => (
                  <option key={acctEnum} value={acctEnum}>
                    {label}
                  </option>
                ))}
              </select>
              {errors.fromAccount && <span>From Account is required</span>}
            </div>
            <div>
              <label>From Currency:</label>
              {/* If fromAccount === "Exchange", user can choose; else read-only */}
              {fromAccount === "Exchange" ? (
                <select {...register("fromCurrency", { required: true })}>
                  <option value="">Select Currency</option>
                  <option value="USD">USD</option>
                  <option value="BTC">BTC</option>
                </select>
              ) : (
                <input type="text" {...register("fromCurrency")} readOnly />
              )}
              {errors.fromCurrency && <span>From Currency is required</span>}
            </div>
            <div>
              <label>Amount (From):</label>
              <input
                type="number"
                step="0.00000001"
                {...register("amountFrom", { required: true, valueAsNumber: true })}
              />
              {errors.amountFrom && <span>Amount (From) is required</span>}
            </div>
            {/* 
              The "toAccount" / "toCurrency" are auto-filled or read-only in this UI.
              We do not store them in the single transaction row, so it's mostly for display.
            */}
            <div>
              <label>To Account:</label>
              <input type="text" {...register("toAccount")} readOnly />
            </div>
            <div>
              <label>To Currency:</label>
              <input type="text" {...register("toCurrency")} readOnly />
            </div>
            <div>
              <label>Amount (To):</label>
              <input
                type="number"
                step="0.00000001"
                {...register("amountTo", { required: true, valueAsNumber: true })}
              />
              {errors.amountTo && <span>Amount (To) is required</span>}
            </div>
            <div>
              <label>Fee (USD):</label>
              <input type="number" step="0.01" {...register("fee", { valueAsNumber: true })} />
            </div>
          </>
        );

      case "Buy":
        return (
          <>
            <div>
              <label>Account:</label>
              <input type="text" value="Exchange" readOnly {...register("account")} />
            </div>
            <div>
              <label>Amount USD:</label>
              <input
                type="number"
                step="0.01"
                {...register("amountUSD", { required: true, valueAsNumber: true })}
              />
              {errors.amountUSD && <span>Amount USD is required</span>}
            </div>
            <div>
              <label>Amount BTC:</label>
              <input
                type="number"
                step="0.00000001"
                {...register("amountBTC", { required: true, valueAsNumber: true })}
              />
              {errors.amountBTC && <span>Amount BTC is required</span>}
            </div>
            <div>
              <label>Fee (USD):</label>
              <input type="number" step="0.01" {...register("fee", { valueAsNumber: true })} />
            </div>
          </>
        );

      case "Sell":
        return (
          <>
            <div>
              <label>Account:</label>
              <input type="text" value="Exchange" readOnly {...register("account")} />
            </div>
            <div>
              <label>Amount BTC:</label>
              <input
                type="number"
                step="0.00000001"
                {...register("amountBTC", { required: true, valueAsNumber: true })}
              />
              {errors.amountBTC && <span>Amount BTC is required</span>}
            </div>
            <div>
              <label>Amount USD:</label>
              <input
                type="number"
                step="0.01"
                {...register("amountUSD", { required: true, valueAsNumber: true })}
              />
              {errors.amountUSD && <span>Amount USD is required</span>}
            </div>
            <div>
              <label>Fee (USD):</label>
              <input type="number" step="0.01" {...register("fee", { valueAsNumber: true })} />
            </div>
          </>
        );

      default:
        return null;
    }
  };

  // (G) Final JSX
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* Transaction Type */}
      <div>
        <label>Transaction Type:</label>
        <select value={currentType} onChange={onTransactionTypeChange} required>
          <option value="">Select Transaction Type</option>
          {Object.entries(transactionTypeLabels).map(([typeEnum, label]) => (
            <option key={typeEnum} value={typeEnum}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {/* Date & Time */}
      <div>
        <label>Date &amp; Time:</label>
        <input
          type="datetime-local"
          {...register("timestamp", { required: "Date & Time is required" })}
        />
        {errors.timestamp && <span>{errors.timestamp.message}</span>}
      </div>

      {/* Dynamic Fields */}
      {renderDynamicFields()}

      <button type="submit">Submit Transaction</button>
    </form>
  );
};

export default TransactionForm;