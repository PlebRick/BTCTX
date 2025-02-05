// BitcoinTX_FastPYthon/frontend/src/components/TransactionForm.tsx

import React, { useState, useEffect } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';

// Define types for transaction types and other options
type TransactionType = 'deposit' | 'withdrawal' | 'transfer' | 'buy' | 'sell';
type AccountType = 'bank' | 'wallet' | 'exchange';
type Currency = 'USD' | 'BTC';
type DepositSource = 'N/A' | 'My BTC' | 'Gift' | 'Income' | 'Interest' | 'Reward';
type WithdrawalPurpose = 'N/A' | 'Spent' | 'Gift' | 'Donation' | 'Lost';

// Define the interface for our form data.
interface TransactionFormData {
  dateTime: string;
  transactionType: TransactionType;
  // For Deposit and Withdrawal
  account?: AccountType;
  currency?: Currency;
  amount?: number;
  fee?: number;
  feeCurrency?: Currency;
  // Deposit-specific:
  source?: DepositSource;
  // Withdrawal-specific:
  purpose?: WithdrawalPurpose;
  // Transfer-specific:
  fromAccount?: AccountType;
  fromCurrency?: Currency;
  amountFrom?: number;
  toAccount?: AccountType;
  toCurrency?: Currency;
  amountTo?: number;
  // Buy and Sell-specific:
  amountUSD?: number;
  amountBTC?: number;
  // For Sell form (optional toggle)
  tradeType?: 'buy' | 'sell';
}

const TransactionForm: React.FC = () => {
  const { register, handleSubmit, watch, setValue, reset } = useForm<TransactionFormData>();
  const [currentType, setCurrentType] = useState<TransactionType | ''>('');
  
  // Watch account selections to adjust currency fields dynamically
  const account = watch('account');
  const fromAccount = watch('fromAccount');
  const toAccount = watch('toAccount');

  // For Deposit or Withdrawal, update currency automatically based on account type
  useEffect(() => {
    if (currentType === 'deposit' || currentType === 'withdrawal') {
      if (account === 'bank') {
        setValue('currency', 'USD');
      } else if (account === 'wallet') {
        setValue('currency', 'BTC');
      }
    }
  }, [account, currentType, setValue]);

  // For Transfer, update fromCurrency and toCurrency based on account selection
  useEffect(() => {
    if (currentType === 'transfer') {
      if (fromAccount === 'bank') {
        setValue('fromCurrency', 'USD');
      } else if (fromAccount === 'wallet') {
        setValue('fromCurrency', 'BTC');
      }
      if (toAccount === 'bank') {
        setValue('toCurrency', 'USD');
      } else if (toAccount === 'wallet') {
        setValue('toCurrency', 'BTC');
      }
    }
  }, [fromAccount, toAccount, currentType, setValue]);

  // When the transaction type changes, reset the form to avoid mixing fields.
  const onTransactionTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedType = e.target.value as TransactionType;
    setCurrentType(selectedType);
    reset({ transactionType: selectedType });
  };

  // Form submission handler
  // Inside TransactionForm.tsx

const onSubmit: SubmitHandler<TransactionFormData> = async (data) => {
  console.log('Submitting transaction data:', data); // For debugging

  try {
    const response = await fetch('http://127.0.0.1:8000/api/transactions/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // If authentication is enforced, replace with a valid token:
        'Authorization': 'Bearer YOUR_TEMP_JWT_TOKEN'
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      // If the response is not ok, throw an error to be caught below.
      throw new Error(`Server error: ${response.status}`);
    }

    const result = await response.json();
    console.log('Transaction created:', result);
    alert('Transaction submitted successfully!');
  } catch (error) {
    console.error('Error submitting transaction:', error);
    alert('Error submitting transaction. Check console for details.');
  }
};

  // Helper to render fee field for all forms
  const renderFeeField = () => (
    <div>
      <label>Fee:</label>
      <input type="number" step="0.00000001" {...register('fee')} />
      <select {...register('feeCurrency')}>
        <option value="">Select Fee Currency</option>
        <option value="USD">USD</option>
        <option value="BTC">BTC</option>
      </select>
    </div>
  );

  // Render the dynamic part of the form based on transaction type
  const renderFormFields = () => {
    switch (currentType) {
      case 'deposit':
        return (
          <div>
            <div>
              <label>Account:</label>
              <select {...register('account', { required: true })}>
                <option value="">Select Account</option>
                <option value="bank">Bank</option>
                <option value="wallet">Wallet</option>
                <option value="exchange">Exchange</option>
              </select>
            </div>
            <div>
              <label>Currency:</label>
              {account === 'bank' && (
                <input type="text" value="USD" readOnly {...register('currency')} />
              )}
              {account === 'wallet' && (
                <input type="text" value="BTC" readOnly {...register('currency')} />
              )}
              {account === 'exchange' && (
                <select {...register('currency', { required: true })}>
                  <option value="">Select Currency</option>
                  <option value="USD">USD</option>
                  <option value="BTC">BTC</option>
                </select>
              )}
            </div>
            <div>
              <label>Amount:</label>
              <input type="number" step="0.00000001" {...register('amount', { required: true })} />
            </div>
            <div>
              <label>Source:</label>
              <select {...register('source', { required: true })}>
                <option value="N/A">N/A</option>
                <option value="My BTC">My BTC</option>
                <option value="Gift">Gift</option>
                <option value="Income">Income</option>
                <option value="Interest">Interest</option>
                <option value="Reward">Reward</option>
              </select>
            </div>
            {renderFeeField()}
          </div>
        );
      case 'withdrawal':
        return (
          <div>
            <div>
              <label>Account:</label>
              <select {...register('account', { required: true })}>
                <option value="">Select Account</option>
                <option value="bank">Bank</option>
                <option value="wallet">Wallet</option>
                <option value="exchange">Exchange</option>
              </select>
            </div>
            <div>
              <label>Currency:</label>
              {account === 'bank' && (
                <input type="text" value="USD" readOnly {...register('currency')} />
              )}
              {account === 'wallet' && (
                <input type="text" value="BTC" readOnly {...register('currency')} />
              )}
              {account === 'exchange' && (
                <select {...register('currency', { required: true })}>
                  <option value="">Select Currency</option>
                  <option value="USD">USD</option>
                  <option value="BTC">BTC</option>
                </select>
              )}
            </div>
            <div>
              <label>Amount:</label>
              <input type="number" step="0.00000001" {...register('amount', { required: true })} />
            </div>
            <div>
              <label>Purpose:</label>
              <select {...register('purpose', { required: true })}>
                <option value="N/A">N/A</option>
                <option value="Spent">Spent</option>
                <option value="Gift">Gift</option>
                <option value="Donation">Donation</option>
                <option value="Lost">Lost</option>
              </select>
            </div>
            {renderFeeField()}
          </div>
        );
      case 'transfer':
        return (
          <div>
            <div>
              <label>From Account:</label>
              <select {...register('fromAccount', { required: true })}>
                <option value="">Select From Account</option>
                <option value="bank">Bank</option>
                <option value="wallet">Wallet</option>
                <option value="exchange">Exchange</option>
              </select>
            </div>
            <div>
              <label>From Currency:</label>
              {fromAccount === 'bank' && (
                <input type="text" value="USD" readOnly {...register('fromCurrency')} />
              )}
              {fromAccount === 'wallet' && (
                <input type="text" value="BTC" readOnly {...register('fromCurrency')} />
              )}
              {fromAccount === 'exchange' && (
                <select {...register('fromCurrency', { required: true })}>
                  <option value="">Select Currency</option>
                  <option value="USD">USD</option>
                  <option value="BTC">BTC</option>
                </select>
              )}
            </div>
            <div>
              <label>Amount (From):</label>
              <input type="number" step="0.00000001" {...register('amountFrom', { required: true })} />
            </div>
            <div>
              <label>To Account:</label>
              <select {...register('toAccount', { required: true })}>
                <option value="">Select To Account</option>
                <option value="bank">Bank</option>
                <option value="wallet">Wallet</option>
                <option value="exchange">Exchange</option>
              </select>
            </div>
            <div>
              <label>To Currency:</label>
              {toAccount === 'bank' && (
                <input type="text" value="USD" readOnly {...register('toCurrency')} />
              )}
              {toAccount === 'wallet' && (
                <input type="text" value="BTC" readOnly {...register('toCurrency')} />
              )}
              {toAccount === 'exchange' && (
                <select {...register('toCurrency', { required: true })}>
                  <option value="">Select Currency</option>
                  <option value="USD">USD</option>
                  <option value="BTC">BTC</option>
                </select>
              )}
            </div>
            <div>
              <label>Amount (To):</label>
              <input type="number" step="0.00000001" {...register('amountTo', { required: true })} />
            </div>
            {renderFeeField()}
          </div>
        );
      case 'buy':
        return (
          <div>
            <div>
              <label>Account:</label>
              <input type="text" value="Exchange" readOnly {...register('account')} />
            </div>
            <div>
              <label>Amount USD:</label>
              <input type="number" step="0.01" {...register('amountUSD', { required: true })} />
            </div>
            <div>
              <label>Amount BTC:</label>
              <input type="number" step="0.00000001" {...register('amountBTC', { required: true })} />
            </div>
            {renderFeeField()}
          </div>
        );
      case 'sell':
        return (
          <div>
            <div>
              <label>Account:</label>
              <input type="text" value="Exchange" readOnly {...register('account')} />
            </div>
            <div>
              <label>Trade Type:</label>
              <div>
                <label>
                  <input type="radio" value="sell" {...register('tradeType', { required: true })} defaultChecked />
                  Sell
                </label>
                <label style={{ marginLeft: '10px' }}>
                  <input type="radio" value="buy" {...register('tradeType', { required: true })} />
                  Buy
                </label>
              </div>
            </div>
            <div>
              <label>Amount BTC:</label>
              <input type="number" step="0.00000001" {...register('amountBTC', { required: true })} />
            </div>
            <div>
              <label>Amount USD:</label>
              <input type="number" step="0.01" {...register('amountUSD', { required: true })} />
            </div>
            {renderFeeField()}
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
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
      <div>
        <label>Date &amp; Time:</label>
        <input type="datetime-local" {...register('dateTime', { required: true })} />
      </div>
      {renderFormFields()}
      <button type="submit">Submit Transaction</button>
    </form>
  );
};

export default TransactionForm;
