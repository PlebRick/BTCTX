import React, { useEffect, useState } from "react";
import "../styles/transactionPanel.css";
import TransactionForm from "./TransactionForm";

/**
 * TransactionPanelProps:
 * Extends your original props with optional "mode" and "existingTransaction"
 * for edit mode support, and preserves isOpen, onClose, onSubmitSuccess from original.
 */
interface TransactionPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmitSuccess?: () => void;

  // NEW: Additional props for create/edit mode
  mode?: "create" | "edit";
  existingTransaction?: ITransaction;
}

const TransactionPanel: React.FC<TransactionPanelProps> = ({
  isOpen,
  onClose,
  onSubmitSuccess,

  // NEW: default mode = "create"
  mode = "create",
  existingTransaction,
}) => {
  // Original local states
  const [showDiscardModal, setShowDiscardModal] = useState(false);
  const [isFormDirty, setIsFormDirty] = useState(false);

  // NEW: track if we’re saving (spinner)
  const [isSaving, setIsSaving] = useState(false);

  /**
   * Keep your original effect: whenever the panel opens,
   * reset discard modal & dirty state, plus reset spinner.
   */
  useEffect(() => {
    if (isOpen) {
      setShowDiscardModal(false);
      setIsFormDirty(false);
      setIsSaving(false); // NEW
    }
  }, [isOpen]);

  /**
   * If user clicks on the overlay, we only close if the form
   * isn't dirty or we confirm discarding changes. If we're saving,
   * we block closing.
   */
  const handleOverlayClick = () => {
    if (isFormDirty && !isSaving) {
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

  /**
   * Called by the form on success—close the panel and let the parent
   * re-fetch data or do whatever it needs.
   */
  const handleFormSubmitSuccess = () => {
    onClose();
    onSubmitSuccess?.();
  };

  /**
   * If the panel is closed, render nothing
   */
  if (!isOpen) return null;

  // NEW: callback from form so we can show a spinner
  const onSavingStateChange = (saving: boolean) => {
    setIsSaving(saving);
  };

  return (
    <>
      {/* Spinner Overlay if saving */}
      {isSaving && (
        <div className="saving-overlay">
          <div className="spinner" />
          <p>Saving changes, please wait...</p>
        </div>
      )}

      {/* Original overlay logic */}
      <div className="transaction-panel-overlay" onClick={handleOverlayClick} />

      <div className="transaction-panel">
        <div className="panel-header">
          {/* Conditionally show Add or Edit */}
          <h2>{mode === "edit" ? "Edit Transaction" : "Add Transaction"}</h2>
        </div>

        <div className="panel-body">
          <TransactionForm
            id="transaction-form"
            onDirtyChange={setIsFormDirty}
            onSubmitSuccess={handleFormSubmitSuccess}

            // NEW: Pass these props to enable edit mode in the form
            mode={mode}
            existingTransaction={existingTransaction}
            onSavingStateChange={onSavingStateChange}
          />
        </div>

        <div className="panel-footer">
          <button
            className="save-button"
            type="submit"
            form="transaction-form"
            disabled={isSaving} // NEW: disable if currently saving
          >
            {mode === "edit" ? "Save Changes" : "Save Transaction"}
          </button>
        </div>
      </div>

      {showDiscardModal && (
        <div className="discard-modal">
          <div className="discard-modal-content">
            <h3>Discard changes?</h3>
            <p>
              Your changes have not been saved. If you close this panel, they will be
              lost.
            </p>
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
