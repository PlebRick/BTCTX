/**
 * TransactionPanel.tsx
 *
 * This component renders a sliding panel for adding a transaction.
 * It includes an overlay, header, body (with the TransactionForm component), 
 * and footer. It also displays a modal to confirm discarding changes.
 *
 * Make sure your tsconfig (specifically tsconfig.app.json) includes:
 *   "jsx": "react-jsx",
 *   "esModuleInterop": true,
 *   "lib": ["DOM", "DOM.Iterable", "ESNext"],
 * so that JSX and global types like Promise and Iterable are recognized.
 */

import * as React from 'react';
import { useState } from 'react';
import TransactionForm from '../components/TransactionForm';
import "../styles/transactionPanel.css";

// A constant for the form element's id, used for associating the submit button.
const FORM_ID = "transaction-form";

const TransactionPanel: React.FC = () => {
  // State to control visibility of the panel and discard modal.
  const [showPanel, setShowPanel] = useState<boolean>(true);
  const [showDiscardModal, setShowDiscardModal] = useState<boolean>(false);

  // Handler for when the overlay is clicked to trigger discard confirmation.
  const handleOverlayClick = () => {
    setShowDiscardModal(true);
  };

  // Handler to cancel discarding changes.
  const handleGoBack = () => {
    setShowDiscardModal(false);
  };

  // Handler to confirm discarding changes and close the panel.
  const handleDiscardChanges = () => {
    setShowDiscardModal(false);
    setShowPanel(false);
  };

  // Handler called when the TransactionForm is successfully submitted.
  const handleFormSubmitSuccess = () => {
    setShowPanel(false);
  };

  if (!showPanel) return null;

  return (
    <>
      <div className="transaction-panel-overlay" onClick={handleOverlayClick}></div>
      <div className="transaction-panel">
        <div className="panel-header">
          <h2>Add Transaction</h2>
        </div>
        <div className="panel-body">
          <TransactionForm id={FORM_ID} onSubmitSuccess={handleFormSubmitSuccess} />
        </div>
        <div className="panel-footer">
          <button className="save-button" type="submit" form={FORM_ID}>
            Save Transaction
          </button>
        </div>
      </div>
      {showDiscardModal && (
        <div className="discard-modal">
          <div className="discard-modal-content">
            <h3>Discard changes?</h3>
            <p>Are you sure you want to discard your changes?</p>
            <div className="discard-modal-actions">
              <button onClick={handleGoBack}>Go back</button>
              <button onClick={handleDiscardChanges} className="danger">
                Discard
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default TransactionPanel;
