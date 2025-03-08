import React, { useState } from "react";
import axios from "axios";
import api from "../api"; // Centralized API client
import "../styles/settings.css"; 

// ✅ Define the API error response type
interface ApiErrorResponse {
  detail?: string;
}

const Settings: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>("");

  // ✅ Function to delete all transactions
  const handleDeleteTransactions = async (): Promise<void> => {
    const confirmed: boolean = window.confirm(
      "Are you sure you want to delete all transactions? This action cannot be undone."
    );
    if (!confirmed) {
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      await api.delete<ApiErrorResponse>("/transactions/delete_all");
      setMessage("All transactions have been successfully deleted.");
    } catch (error: unknown) {
      console.error("Error deleting transactions:", error);
      if (axios.isAxiosError<ApiErrorResponse>(error)) {
        const detailMsg: string | undefined = error.response?.data?.detail;
        const fallbackMsg: string = error.message || "Failed to delete transactions.";
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
    <div className="settings-container">
      <h2 className="settings-title">Settings</h2>

      {/* ✅ Data Management */}
      <div className="settings-section">
        <div className="settings-option">
          <div>
            <span className="settings-option-title">Delete All Transactions</span>
            <p className="settings-option-subtitle">This action cannot be undone.</p>
          </div>
          <button
            onClick={handleDeleteTransactions}
            disabled={loading}
            className="settings-button danger"
          >
            {loading ? "Deleting..." : "Delete"}
          </button>
        </div>
        {message && <p className="settings-message">{message}</p>}
      </div>

      {/* ✅ Account Section */}
      <div className="settings-section">
        <h3>Account</h3>
        <div className="settings-option">
          <div>
            <span className="settings-option-title">Logout</span>
            <p className="settings-option-subtitle">Sign out of your account.</p>
          </div>
          <button className="settings-button">Logout</button>
        </div>
        <div className="settings-option">
          <div>
            <span className="settings-option-title">Reset Account</span>
            <p className="settings-option-subtitle">Reset your account data.</p>
          </div>
          <button className="settings-button">Reset</button>
        </div>
      </div>

      {/* ✅ Application Section */}
      <div className="settings-section">
        <h3>Application</h3>
        <div className="settings-option">
          <div>
            <span className="settings-option-title">Uninstall</span>
            <p className="settings-option-subtitle">Remove the application.</p>
          </div>
          <button className="settings-button danger">Uninstall</button>
        </div>
      </div>
    </div>
  );
};

export default Settings;
