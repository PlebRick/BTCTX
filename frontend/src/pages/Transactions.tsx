// src/pages/Transactions.tsx
import React from 'react';

const Transactions: React.FC = () => {
  return (
    <div>
      <h2>Transactions</h2>
      <button className="btn">Add Transaction</button>

      {/* You can later place your transaction listing code here.
          For instance, <TransactionList /> or inline logic. */}
    </div>
  );
};

export default Transactions;