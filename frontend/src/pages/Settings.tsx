import React, { useState } from 'react';
import axios from 'axios';
import api from '../api'; // Centralized API client

const Settings: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>("");

  const handleDeleteTransactions = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to delete all transactions? This action cannot be undone."
    );
    if (!confirmed) {
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      await api.delete('/transactions/delete_all');
      setMessage("All transactions have been successfully deleted.");
    } catch (error: unknown) {
      console.error("Error deleting transactions:", error);
      if (axios.isAxiosError<ApiErrorResponse>(error)) {
        // error.response?.data is now seen as ApiErrorResponse (or undefined)
        const detailMsg = error.response?.data?.detail;
        const fallbackMsg = error.message || "Failed to delete transactions.";
        setMessage(detailMsg ?? fallbackMsg);
      } else if (error instanceof Error) {
        setMessage(error.message);
      } else {
        setMessage("An unknown error occurred while deleting transactions.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "1rem" }}>
      <p>Manage your user settings here.</p>
      <hr />
      <div>
        <h3>Data Management</h3>
        <button
          onClick={handleDeleteTransactions}
          disabled={loading}
          style={{ padding: "0.5rem 1rem" }}
        >
          {loading ? "Deleting Transactions..." : "Delete All Transactions"}
        </button>
        {message && <p>{message}</p>}
      </div>
    </div>
  );
};

export default Settings;
