import React, { useEffect, useState } from 'react';
import '../styles/transactionPanel.css';

interface TransactionPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const TransactionPanel: React.FC<TransactionPanelProps> = ({ isOpen, onClose }) => {
  // Track if the form has been modified
  const [isDirty, setIsDirty] = useState(false);

  // Track whether the discard confirmation modal is open
  const [showDiscardModal, setShowDiscardModal] = useState(false);

  // If the panel just opened, reset everything
  useEffect(() => {
    if (isOpen) {
      setIsDirty(false);
      setShowDiscardModal(false);
    }
  }, [isOpen]);

  // Handle the overlay click
  const handleOverlayClick = () => {
    // If form is not dirty, close immediately
    if (!isDirty) {
      onClose();
    } else {
      // Show discard confirmation
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

  // Placeholder "save" action
  const handleSave = () => {
    console.log('TODO: Handle actual form submission...');
    // After saving, we can close the panel or reset the form
    onClose();
  };

  // For demonstration, if user types anything in this input, mark form as dirty
  const handleInputChange = () => {
    setIsDirty(true);
  };

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

        {/* Main content area -- currently empty aside from one input */}
        <div className="panel-body">
          {/* Placeholder input to demonstrate "isDirty" logic */}
          <label>Example Input:</label>
          <input 
            type="text"
            placeholder="Type something..."
            onChange={handleInputChange}
          />
        </div>

        {/* Bottom area with "Save Transaction" */}
        <div className="panel-footer">
          <button className="save-button" onClick={handleSave}>
            Save Transaction
          </button>
        </div>
      </div>

      {/* Discard changes confirmation modal */}
      {showDiscardModal && (
        <div className="discard-modal">
          <div className="discard-modal-content">
            <h3>Discard changes?</h3>
            <p>Your changes have not been saved and will be discarded if you move away from this page.</p>
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