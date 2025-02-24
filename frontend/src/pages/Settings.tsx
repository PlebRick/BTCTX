// src/pages/Settings.tsx
import React, { useState } from 'react';
import axios from 'axios';

const Settings: React.FC = () => {
  // Local state for loading and displaying a message (success or error)
  const [loading, setLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>("");

  /**
   * handleDeleteTransactions
   *
   * This function is called when the "Delete All Transactions" button is clicked.
   * It shows a confirmation dialog and, if confirmed, sends a DELETE request to the backend
   * endpoint to delete all Transaction records.
   */
  const handleDeleteTransactions = async () => {
    // Display a confirmation prompt to ensure the user wants to proceed.
    const confirmed = window.confirm(
      "Are you sure you want to delete all transactions? This action cannot be undone."
    );
    if (!confirmed) {
      return; // Exit if the user cancels.
    }
    
    // Set loading state and clear any previous messages.
    setLoading(true);
    setMessage("");
    
    try {
      // Send a DELETE request to the backend endpoint.
      // Adjust the URL as needed to match your backend configuration.
      await axios.delete("http://127.0.0.1:8000/api/transactions/delete_all");
      
      // If successful, set a success message.
      setMessage("All transactions have been successfully deleted.");
    } catch (error: unknown) {
      console.error("Error deleting transactions:", error);
      // Use type guards to handle the error without using 'any'
      if (axios.isAxiosError(error)) {
        setMessage(error.response?.data?.detail || error.message || "Failed to delete transactions.");
      } else if (error instanceof Error) {
        setMessage(error.message);
      } else {
        setMessage("An unknown error occurred while deleting transactions.");
      }
    } finally {
      // Reset loading state once the request is finished.
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "1rem" }}>
      <p>Manage your user settings here.</p>
      <hr />
      {/* Data Management Section */}
      <div>
        <h3>Data Management</h3>
        {/* Delete All Transactions Button */}
        <button
          onClick={handleDeleteTransactions}
          disabled={loading}
          style={{ padding: "0.5rem 1rem" }}
        >
          {loading ? "Deleting Transactions..." : "Delete All Transactions"}
        </button>
        {/* Display success or error message */}
        {message && <p>{message}</p>}
      </div>
    </div>
  );
};

export default Settings;