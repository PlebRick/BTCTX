// src/pages/Transactions.tsx
import React, { useState } from 'react';
import TransactionPanel from '../components/TransactionPanel';

const Transactions: React.FC = () => {
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  const openPanel = () => {
    setIsPanelOpen(true);
  };

  const closePanel = () => {
    setIsPanelOpen(false);
  };

  return (
    <div>
      <button className="accent-btn" onClick={openPanel}>
        Add Transaction
      </button>
      <br></br>
      <br></br>
      <br></br>

      {/* Here you’d eventually render your transaction listing/table */}
      <p>List of transactions will go here (placeholder).</p>

      {/* The transaction panel is controlled at this page level */}
      <TransactionPanel
        isOpen={isPanelOpen}
        onClose={closePanel}
      />
    </div>
  );
};

export default Transactions;