import React, { useEffect, useState } from 'react';
import '../styles/transactionPanel.css'; // Keep your existing CSS import

// (NEW) Import your real TransactionForm
import TransactionForm from '../components/TransactionForm';

interface TransactionPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const TransactionPanel: React.FC<TransactionPanelProps> = ({ isOpen, onClose }) => {
  // Track if the form has been modified (dirty)
  const [isFormDirty, setIsFormDirty] = useState(false);

  // Track whether the discard confirmation modal is open
  const [showDiscardModal, setShowDiscardModal] = useState(false);

  // If the panel just opened, reset everything
  useEffect(() => {
    if (isOpen) {
      setIsFormDirty(false);
      setShowDiscardModal(false);
    }
  }, [isOpen]);

  // ------------------------------------------------------------
  // (A) Overly click logic:
  //     If form is not dirty -> close immediately.
  //     If form is dirty -> show discard confirmation.
  // ------------------------------------------------------------
  const handleOverlayClick = () => {
    if (!isFormDirty) {
      onClose();
    } else {
      setShowDiscardModal(true);
    }
  };

  // "Discard changes" action => close panel
  const handleDiscardChanges = () => {
    setShowDiscardModal(false);
    onClose();
  };

  // "Go back" => close the discard modal, keep panel open
  const handleGoBack = () => {
    setShowDiscardModal(false);
  };

  // ------------------------------------------------------------
  // (B) Called from TransactionForm after a successful POST
  //     -> close this panel so user sees the updated list
  // ------------------------------------------------------------
  const handleFormSubmitSuccess = () => {
    onClose();
  };

  // ------------------------------------------------------------
  // (C) We'll rely on the form's "id" to let our panel's 
  //     "Save Transaction" button trigger a submit.
  // ------------------------------------------------------------
  const FORM_ID = "transactionFormId";

  // Panel & overlay should only render if isOpen is true
  if (!isOpen) return null;

  return (
    <>
      {/* Overlay that dims the rest of the app */}
      <div className="transaction-panel-overlay" onClick={handleOverlayClick}></div>

      <div className="transaction-panel">
        {/* Title / Header */}
        <div className="panel-header">
          <h2>Add Transaction</h2>
        </div>

        {/* Main content area -- now containing the REAL TransactionForm */}
        <div className="panel-body">
          <TransactionForm
            // The form uses an id so the panel button can submit it
            // see (E) below.
            // We'll also pass our isDirty callback & submit success callback
            onDirtyChange={(dirty) => setIsFormDirty(dirty)}
            onSubmitSuccess={handleFormSubmitSuccess}
          />
        </div>

        {/* Bottom area with "Save Transaction" */}
        <div className="panel-footer">
          {/* 
            (D) We reference the form by "form=FORM_ID" 
            and specify type="submit". 
            This means clicking this button will submit 
            the form that has id={FORM_ID} in TransactionForm.
          */}
          <button 
            className="save-button" 
            form={FORM_ID} 
            type="submit"
          >
            Save Transaction
          </button>
        </div>
      </div>

      {/* (E) Discard changes confirmation modal */}
      {showDiscardModal && (
        <div className="discard-modal">
          <div className="discard-modal-content">
            <h3>Discard changes?</h3>
            <p>
              Your changes have not been saved and will be discarded if you move away 
              from this page.
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