import React, { useEffect, useState } from "react";
import "../styles/transactionPanel.css";
import TransactionForm from "./TransactionForm";

/**
 * TransactionPanelProps:
 * - isOpen: Whether the sliding panel is open/visible.
 * - onClose: Function to close the panel.
 * - onSubmitSuccess: Callback after a successful transaction submission.
 */
interface TransactionPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmitSuccess?: () => void;
}

/**
 * TransactionPanel
 * Shows a sliding panel with an overlay, containing the TransactionForm inside.
 * Uses a custom 'Save' button in the footer to submit the form by referencing
 * the form's 'id' prop.
 */
const TransactionPanel: React.FC<TransactionPanelProps> = ({
  isOpen,
  onClose,
  onSubmitSuccess,
}) => {
  // Whether to show a discard-changes confirmation modal
  const [showDiscardModal, setShowDiscardModal] = useState(false);

  // Track if the form is dirty (unsaved changes)
  const [isFormDirty, setIsFormDirty] = useState(false);

  /**
   * Whenever the panel opens, reset the discard modal and
   * mark the form as not dirty.
   */
  useEffect(() => {
    if (isOpen) {
      setShowDiscardModal(false);
      setIsFormDirty(false);
    }
  }, [isOpen]);

  /**
   * Clicking the overlay:
   * If the form is dirty => show discard confirmation.
   * Else, close immediately.
   */
  const handleOverlayClick = () => {
    if (isFormDirty) {
      setShowDiscardModal(true);
    } else {
      onClose();
    }
  };

  /** Close panel and discard changes. */
  const handleDiscardChanges = () => {
    setShowDiscardModal(false);
    onClose();
  };

  /** Go back to panel (cancel discard). */
  const handleGoBack = () => {
    setShowDiscardModal(false);
  };

  /** Called after successful form submission (POST) in TransactionForm. */
  const handleFormSubmitSuccess = () => {
    // Close panel
    onClose();
    // Notify parent if needed
    onSubmitSuccess?.();
  };

  // If panel is not open, return null to remove it from DOM
  if (!isOpen) return null;

  return (
    <>
      {/* Overlay (click to potentially discard) */}
      <div className="transaction-panel-overlay" onClick={handleOverlayClick}></div>

      {/* Sliding panel container */}
      <div className="transaction-panel">
        {/* Header */}
        <div className="panel-header">
          <h2>Add Transaction</h2>
        </div>

        {/* Body: holds the TransactionForm */}
        <div className="panel-body">
          {/*
            We pass:
            - id="transaction-form" so we can reference it in the Save button below.
            - onDirtyChange => setIsFormDirty to track unsaved changes.
            - onSubmitSuccess => handleFormSubmitSuccess to close panel on success.
          */}
          <TransactionForm
            id="transaction-form"
            onDirtyChange={setIsFormDirty}
            onSubmitSuccess={handleFormSubmitSuccess}
          />
        </div>

        {/* Footer with a custom 'Save Transaction' button */}
        <div className="panel-footer">
          {/*
            This button triggers the form submission by referencing form="transaction-form"
            and type="submit", so it acts like a submit button for that specific form.
          */}
          <button
            className="save-button"
            type="submit"
            form="transaction-form"
          >
            Save Transaction
          </button>
        </div>
      </div>

      {/* Discard-changes confirmation modal */}
      {showDiscardModal && (
        <div className="discard-modal">
          <div className="discard-modal-content">
            <h3>Discard changes?</h3>
            <p>
              Your changes have not been saved. If you close this panel, they will be lost.
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
