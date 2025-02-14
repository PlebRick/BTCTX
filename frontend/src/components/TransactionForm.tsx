import React, { useState, useEffect } from "react";
import { useForm, SubmitHandler } from "react-hook-form";
import axios from "axios";

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
  source?: DepositSource;          // For deposit
  purpose?: WithdrawalPurpose;     // For withdrawal
  fee?: number;                    // Always in USD
  costBasisUSD?: number;           // For BTC deposits

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
// 4) TransactionForm Component
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

  // 1) Create a local variable to store the "fromCurrency" value from the form.
//    This way, we can reference it easily in our effect below.
const fromCurrencyVal = watch("fromCurrency");

// 2) Auto-set fromCurrency/toCurrency for Transfers.
//
// This effect runs whenever:
//   - The transaction type (`currentType`) changes
//   - The "fromAccount" field changes
//   - The user changes the "fromCurrency" for "Exchange"
//
// By watching these dependencies, we ensure that when the user picks
// "Exchange" and then chooses "USD" or "BTC", the effect re-runs
// and sets the correct destination (toAccount/toCurrency).
useEffect(() => {
  // If the selected transaction type is NOT "Transfer," do nothing.
  if (currentType !== "Transfer") return;

  // CASE A: User picked "Bank" for fromAccount.
  //   - The only currency for a bank is USD.
  //   - The receiving account is always "Exchange" with "USD".
  if (fromAccount === "Bank") {
    setValue("fromCurrency", "USD");   // Bank -> fromCurrency=USD
    setValue("toAccount", "Exchange"); // toAccount=Exchange
    setValue("toCurrency", "USD");     // Exchange side is also USD
  }

  // CASE B: User picked "Wallet" for fromAccount.
  //   - The only currency for a wallet is BTC.
  //   - The receiving account is always "Exchange" with "BTC".
  else if (fromAccount === "Wallet") {
    setValue("fromCurrency", "BTC");   // Wallet -> fromCurrency=BTC
    setValue("toAccount", "Exchange"); // toAccount=Exchange
    setValue("toCurrency", "BTC");     // Exchange side is also BTC
  }

  // CASE C: User picked "Exchange" for fromAccount.
  //   - We don't *assume* a currency, because the Exchange can do both USD & BTC.
  //   - The user picks fromCurrency in a dropdown, so we read the current value 
  //     from our local "fromCurrencyVal".
  //   - Then we auto-populate the receiving side based on that choice.
  else if (fromAccount === "Exchange") {
    if (fromCurrencyVal === "USD") {
      // If Exchange side is sending USD, the destination is a Bank (USD).
      setValue("toAccount", "Bank");
      setValue("toCurrency", "USD");
    } else if (fromCurrencyVal === "BTC") {
      // If Exchange side is sending BTC, the destination is a Wallet (BTC).
      setValue("toAccount", "Wallet");
      setValue("toCurrency", "BTC");
    }
  }
}, [
  // This is the list of dependencies that re-trigger the effect if any change:
  currentType,     // If the user changes the transaction type away from Transfer, skip.
  fromAccount,     // If the user changes the 'fromAccount' select (Bank, Wallet, Exchange).
  fromCurrencyVal, // If the user changes the 'fromCurrency' while on Exchange, we update toAccount/toCurrency.
  setValue         // We need setValue in scope to actually set the form fields.
]);

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
        // Single-record model: store only the "from" side
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

      reset();
      setCurrentType("");
      alert("Transaction created successfully!");
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        console.error("Axios error creating transaction:", error.response?.data);
        const message = error.response?.data?.detail || error.message || "An error occurred";
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

            {/* We auto-populate the toAccount/toCurrency, just for display */}
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

  // (G) Return the JSX form
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
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

      <div>
        <label>Date & Time:</label>
        <input
          type="datetime-local"
          {...register("timestamp", { required: "Date & Time is required" })}
        />
        {errors.timestamp && <span>{errors.timestamp.message}</span>}
      </div>

      {/* Render fields specific to the chosen transaction type */}
      {renderDynamicFields()}

      <button type="submit">Submit Transaction</button>
    </form>
  );
};

export default TransactionForm;