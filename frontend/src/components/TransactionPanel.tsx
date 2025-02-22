/**
 * TransactionPanel.tsx
 *
 * A sliding panel containing the TransactionForm. The user
 * can open this panel to create or edit a transaction. 
 * We keep the same UI/UX: a discard-changes modal if the form is dirty,
 * a Save button that triggers form submission, etc.
 *
 * Our double-entry backend doesn't force any changes here; 
 * we only ensure the form properly talks to the new multi-line logic 
 * in the service. The user sees a single transaction concept.
 */

import React, { useEffect, useState } from "react";
import "../styles/transactionPanel.css";
import TransactionForm from "./TransactionForm";

interface TransactionPanelProps {
  isOpen: boolean;                 // whether the panel is visible
  onClose: () => void;            // callback to close the panel
  onSubmitSuccess?: () => void;   // callback after a successful transaction submission
}

/**
 * TransactionPanel:
 * - Overlays the screen when open
 * - Holds our TransactionForm
 * - Has a "Save Transaction" button that references the form's 'id'
 */
const TransactionPanel: React.FC<TransactionPanelProps> = ({
  isOpen,
  onClose,
  onSubmitSuccess,
}) => {
  // Whether to show a discard-changes modal
  const [showDiscardModal, setShowDiscardModal] = useState(false);

  // Whether the form is dirty (unsaved changes)
  const [isFormDirty, setIsFormDirty] = useState(false);

  /**
   * Whenever the panel opens, reset the discard modal
   * and mark form as not dirty.
   */
  useEffect(() => {
    if (isOpen) {
      setShowDiscardModal(false);
      setIsFormDirty(false);
    }
  }, [isOpen]);

  /**
   * If the user clicks the overlay while form is dirty, 
   * show a discard confirmation.
   */
  const handleOverlayClick = () => {
    if (isFormDirty) {
      setShowDiscardModal(true);
    } else {
      onClose();
    }
  };

  /**
   * Close panel & discard changes
   */
  const handleDiscardChanges = () => {
    setShowDiscardModal(false);
    onClose();
  };

  /**
   * Cancel discarding, go back to the panel
   */
  const handleGoBack = () => {
    setShowDiscardModal(false);
  };

  /**
   * After the form successfully submits a transaction,
   * we close the panel and optionally notify the parent.
   */
  const handleFormSubmitSuccess = () => {
    onClose();
    onSubmitSuccess?.();
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay: if user clicks it, possibly show discard modal */}
      <div className="transaction-panel-overlay" onClick={handleOverlayClick} />

      {/* Sliding panel container */}
      <div className="transaction-panel">
        <div className="panel-header">
          <h2>Add Transaction</h2>
        </div>

        {/* 
          Panel body holds the TransactionForm.
          We pass id="transaction-form" so we can reference it in the 
          Save button's 'form' attribute. 
          onDirtyChange => track if form is dirty, 
          onSubmitSuccess => close panel after successful submit 
        */}
        <div className="panel-body">
          <TransactionForm
            id="transaction-form"
            onDirtyChange={setIsFormDirty}
            onSubmitSuccess={handleFormSubmitSuccess}
          />
        </div>

        <div className="panel-footer">
          {/**
           * The "Save Transaction" button references form="transaction-form"
           * and type="submit", so it triggers that form's onSubmit.
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

      {showDiscardModal && (
        <div className="discard-modal">
          <div className="discard-modal-content">
            <h3>Discard changes?</h3>
            <p>Your changes have not been saved. If you close this panel, they will be lost.</p>
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
