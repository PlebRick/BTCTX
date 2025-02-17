import React, { useEffect, useState } from "react";
import "../styles/transactionPanel.css";
import TransactionForm from "../components/TransactionForm";

interface TransactionPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmitSuccess?: () => void;
}

/**
 * TransactionPanel
 * Shows a sliding panel with an overlay, containing TransactionForm inside.
 */
const TransactionPanel: React.FC<TransactionPanelProps> = ({
  isOpen,
  onClose,
  onSubmitSuccess,
}) => {
  // Whether to show a discard-changes confirmation modal
  const [showDiscardModal, setShowDiscardModal] = useState(false);
  // Track whether the form is dirty (unsaved changes)
  const [isFormDirty, setIsFormDirty] = useState(false);

  // Reset everything when panel opens
  useEffect(() => {
    if (isOpen) {
      setShowDiscardModal(false);
      setIsFormDirty(false);
    }
  }, [isOpen]);

  /**
   * Clicking the overlay => if form has unsaved changes, show discard modal.
   * Otherwise close the panel directly.
   */
  const handleOverlayClick = () => {
    if (isFormDirty) {
      setShowDiscardModal(true);
    } else {
      onClose();
    }
  };

  /** Discard changes => close panel */
  const handleDiscardChanges = () => {
    setShowDiscardModal(false);
    onClose();
  };

  /** Cancel discard => keep panel open */
  const handleGoBack = () => {
    setShowDiscardModal(false);
  };

  /** Called after a successful transaction submission in TransactionForm */
  const handleFormSubmitSuccess = () => {
    onClose();         // Close panel
    onSubmitSuccess?.();
  };

  // If panel is closed, render nothing
  if (!isOpen) return null;

  return (
    <>
      {/* Overlay (click to discard or close) */}
      <div className="transaction-panel-overlay" onClick={handleOverlayClick}></div>

      {/* Sliding panel */}
      <div className="transaction-panel">
        {/* Header */}
        <div className="panel-header">
          <h2>Add Transaction</h2>
        </div>

        {/* Body with TransactionForm */}
        <div className="panel-body">
          {/* 
            Pass an `id` prop to TransactionForm so the form has <form id="transaction-form" ...>
            Also pass onDirtyChange so we can track unsaved changes.
          */}
          <TransactionForm
            id="transaction-form"
            onDirtyChange={(dirty) => setIsFormDirty(dirty)}
            onSubmitSuccess={handleFormSubmitSuccess}
          />
        </div>

        {/* Footer with a Save button that submits the form above */}
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

      {/* Discard-changes modal */}
      {showDiscardModal && (
        <div className="discard-modal">
          <div className="discard-modal-content">
            <h3>Discard changes?</h3>
            <p>
              Your changes have not been saved and will be discarded if you close this panel.
            </p>
            <div className="discard-modal-actions">
              <button onClick={handleGoBack}>Go back</button>
              <button onClick={handleDiscardChanges} className="danger">
                Discard changes
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default TransactionPanel;
