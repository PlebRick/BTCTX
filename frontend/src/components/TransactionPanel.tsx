import React, { useEffect, useState } from "react";
import "../styles/transactionPanel.css";
import TransactionForm from "./TransactionForm";

/**
 * TransactionPanelProps:
 *  - isOpen: if the panel is visible
 *  - onClose: function to close
 *  - onSubmitSuccess: callback after form success
 */
interface TransactionPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmitSuccess?: () => void;
}

const TransactionPanel: React.FC<TransactionPanelProps> = ({
  isOpen,
  onClose,
  onSubmitSuccess,
}) => {
  const [showDiscardModal, setShowDiscardModal] = useState(false);
  const [isFormDirty, setIsFormDirty] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setShowDiscardModal(false);
      setIsFormDirty(false);
    }
  }, [isOpen]);

  const handleOverlayClick = () => {
    if (isFormDirty) {
      setShowDiscardModal(true);
    } else {
      onClose();
    }
  };

  const handleDiscardChanges = () => {
    setShowDiscardModal(false);
    onClose();
  };

  const handleGoBack = () => {
    setShowDiscardModal(false);
  };

  const handleFormSubmitSuccess = () => {
    onClose();
    onSubmitSuccess?.();
  };

  if (!isOpen) return null;

  return (
    <>
      <div className="transaction-panel-overlay" onClick={handleOverlayClick}></div>

      <div className="transaction-panel">
        <div className="panel-header">
          <h2>Add Transaction</h2>
        </div>

        <div className="panel-body">
          <TransactionForm
            id="transaction-form"
            onDirtyChange={setIsFormDirty}
            onSubmitSuccess={handleFormSubmitSuccess}
          />
        </div>

        <div className="panel-footer">
          <button
            className="save-button"
            type="submit"
            form="transaction-form"
          >
            Save Transaction
          </button>
        </div>
      </div>

      {showDiscardModal && (
        <div className="discard-modal">
          <div className="discard-modal-content">
            <h3>Discard changes?</h3>
            <p>Your changes have not been saved. Closing will lose them.</p>
            <div className="discard-modal-actions">
              <button onClick={handleGoBack}>Go Back</button>
              <button onClick={handleDiscardChanges} className="danger">
                Discard Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default TransactionPanel;
