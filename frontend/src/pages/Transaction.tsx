// frontend/src/pages/Transaction.tsx
import React from 'react';
import TransactionForm from '../components/TransactionForm';

const TransactionPage: React.FC = () => {
  return (
    <div>
      <h1>Transaction Page</h1>
      {/* This renders the dynamic transaction form */}
      <TransactionForm />
    </div>
  );
};

export default TransactionPage;
