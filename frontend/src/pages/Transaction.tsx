// frontend/src/pages/Transaction.tsx

import React from 'react';
import TransactionForm from '../components/TransactionForm';

const TransactionPage: React.FC = () => {
  return (
    <div>
      <h1>Manage Transactions</h1>
      <TransactionForm />
    </div>
  );
};

export default TransactionPage;
