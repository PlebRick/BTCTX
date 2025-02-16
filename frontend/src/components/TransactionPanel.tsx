import React, { useEffect, useState } from 'react';
import '../styles/transactionPanel.css';
import TransactionForm from '../components/TransactionForm';

/**
 * TransactionPanelProps
 * - isOpen: controls the panel visibility
 * - onClose: callback to close the panel
 * - onSubmitSuccess: optional callback after a successful transaction post
 */
interface TransactionPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmitSuccess?: () => void;
}

/**
 * TransactionPanel
 * Renders a sliding panel with an overlay, showing TransactionForm inside.
 * This panel is agnostic to single or double-entry; the new TransactionForm handles that logic.
 */
const TransactionPanel: React.FC<TransactionPanelProps> = ({
  isOpen,
  onClose,
  onSubmitSuccess,
}) => {
  // Tracks if the form is dirty (user has unsaved changes).
  const [isFormDirty, setIsFormDirty] = useState(false);

  // Whether to show a discard-changes confirmation modal
  const [showDiscardModal, setShowDiscardModal] = useState(false);

  // Reset everything when panel first opens
  useEffect(() => {
    if (isOpen) {
      setIsFormDirty(false);
      setShowDiscardModal(false);
    }
  }, [isOpen]);

  /**
   * Handle clicking the overlay:
   * If the form is not dirty => close immediately.
   * If the form is dirty => show discard confirmation.
   */
  const handleOverlayClick = () => {
    if (!isFormDirty) {
      onClose();
    } else {
      setShowDiscardModal(true);
    }
  };

  /**
   * Discard changes => close panel
   */
  const handleDiscardChanges = () => {
    setShowDiscardModal(false);
    onClose();
  };

  /**
   * Cancel discard => keep panel open
   */
  const handleGoBack = () => {
    setShowDiscardModal(false);
  };

  /**
   * Called after TransactionForm successfully posts a transaction
   */
  const handleFormSubmitSuccess = () => {
    // Close the panel
    onClose();
    // Notify parent if provided
    onSubmitSuccess?.();
  };

  // We'll reference the form by this ID
  const FORM_ID = "transactionFormId";

  // If not open, render nothing
  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div className="transaction-panel-overlay" onClick={handleOverlayClick}></div>

      <div className="transaction-panel">
        {/* Header */}
        <div className="panel-header">
          <h2>Add Transaction</h2>
        </div>

        {/* Body: Our double-entry TransactionForm */}
        <div className="panel-body">
          <TransactionForm
            id={FORM_ID}
            onDirtyChange={(dirty) => setIsFormDirty(dirty)}
            onSubmitSuccess={handleFormSubmitSuccess}
          />
        </div>

        {/* Footer with a Save button that submits the form */}
        <div className="panel-footer">
          <button 
            className="save-button"
            form={FORM_ID} 
            type="submit"
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