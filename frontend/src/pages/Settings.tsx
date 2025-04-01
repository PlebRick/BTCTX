// FILE: frontend/src/pages/Settings.tsx

import React, { useState } from "react";
import api from "../api";   // your centralized Axios client
import "../styles/settings.css";

// (Optional) If you have a specific shape for error responses:
interface ApiErrorResponse {
  detail?: string;
}

const Settings: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  /**
   * Fetch the first user's ID (single-user assumption).
   */
  const getUserId = async (): Promise<number | null> => {
    try {
      const res = await api.get("/users"); // Should return an array
      const users = res.data as { id: number; username: string }[];
      return users.length > 0 ? users[0].id : null;
    } catch (err) {
      console.error("Failed to fetch user:", err);
      return null;
    }
  };

  /**
   * Logs out by calling /api/logout, then redirects to /login.
   */
  const logoutAndRedirect = async () => {
    try {
      await api.post("/logout", {}, { withCredentials: true });
      window.location.href = "/login";
    } catch (err) {
      console.error("Logout failed:", err);
      setMessage("Failed to log out. Please try again.");
    }
  };

  /**
   * 1) Logout
   */
  const handleLogout = async () => {
    if (!window.confirm("Are you sure you want to log out?")) return;
    setLoading(true);
    setMessage("");

    await logoutAndRedirect();
    setLoading(false);
  };

  /**
   * 2) Reset Username & Password (keep transactions)
   */
  const handleResetCredentials = async () => {
    const confirmMsg = 
      "This will reset your username and password, but keep existing transactions.\n\nContinue?";
    if (!window.confirm(confirmMsg)) return;

    setLoading(true);
    setMessage("");

    try {
      const userId = await getUserId();
      if (!userId) {
        setMessage("No user found to reset credentials.");
        return;
      }

      const newUsername = prompt("Enter new username", "NewUser");
      if (!newUsername) {
        setMessage("Username reset canceled.");
        return;
      }

      const newPassword = prompt("Enter new password", "Pass1234!");
      if (!newPassword) {
        setMessage("Password reset canceled.");
        return;
      }

      await api.patch(`/users/${userId}`, {
        username: newUsername,
        password: newPassword
      });

      setMessage("Credentials reset. Please log in again.");
    } catch (error) {
      console.error("Error resetting credentials:", error);
      setMessage("Failed to reset credentials.");
    } finally {
      setLoading(false);
    }
  };

  /**
   * 3) Delete All Transactions
   */
  const handleDeleteTransactions = async () => {
    if (!window.confirm("Delete ALL transactions? This cannot be undone.")) return;

    setLoading(true);
    setMessage("");

    try {
      await api.delete<ApiErrorResponse>("/transactions/delete_all");
      setMessage("All transactions deleted.");
    } catch (error) {
      console.error("Error deleting transactions:", error);

      // If you want to handle axios errors specifically:
      // if (axios.isAxiosError<ApiErrorResponse>(error)) {
      //   setMessage(error.response?.data?.detail ?? "Failed to delete transactions.");
      // } else if (error instanceof Error) {
      //   setMessage(error.message);
      // } else {
      //   setMessage("Unknown error while deleting transactions.");
      // }

      // Simpler fallback:
      setMessage(error instanceof Error ? error.message : "Failed to delete transactions.");
    } finally {
      setLoading(false);
    }
  };

  /**
   * 4) Reset Account (delete transactions + delete user + logout → /register)
   */
  const handleResetAccount = async () => {
    const confirmMsg = 
      "This will delete ALL transactions AND your user account.\n\n" +
      "Continue? You’ll be redirected to /register after reset.";
    if (!window.confirm(confirmMsg)) return;
  
    setLoading(true);
    setMessage("");
  
    try {
      // 1) Logout first to clear session
      await api.post("/logout", {}, { withCredentials: true });
  
      // 2) Delete transactions
      await api.delete("/transactions/delete_all");
  
      // 3) Delete the user
      const userId = await getUserId();
      if (userId) {
        await api.delete(`/users/${userId}`);
      }
  
      // 4) Redirect
      setMessage("Account reset. Redirecting to register...");
      window.location.href = "/register";
    } catch (error) {
      console.error("Reset account error:", error);
      setMessage("Failed to reset account. See console for details.");
    } finally {
      setLoading(false);
    }
  };

  // Return valid JSX (ReactNode). This is crucial!
  return (
    <div className="settings-container">
      <h2 className="settings-title">Settings</h2>

      {/* Account Section */}
      <div className="settings-section">
        <h3>Account</h3>
        <div className="settings-option">
          <div className="option-info">
            <span className="settings-option-title">Logout</span>
            <p className="settings-option-subtitle">
              Sign out of your account.
            </p>
          </div>
          <button
            onClick={handleLogout}
            disabled={loading}
            className="settings-button"
          >
            {loading ? "Processing..." : "Logout"}
          </button>
        </div>

        <div className="settings-option">
          <div className="option-info">
            <span className="settings-option-title">Reset Username &amp; Password</span>
            <p className="settings-option-subtitle">
              Change your username and password without deleting any transactions.
            </p>
          </div>
          <button
            onClick={handleResetCredentials}
            disabled={loading}
            className="settings-button"
          >
            {loading ? "Processing..." : "Change"}
          </button>
        </div>
      </div>

      {/* Data Management Section */}
      <div className="settings-section">
        <h3>Data Management</h3>
        <div className="settings-option">
          <div className="option-info">
            <span className="settings-option-title">Delete All Transactions</span>
            <p className="settings-option-subtitle">
              Remove all transaction history. This action cannot be undone.
            </p>
          </div>
          <button
            onClick={handleDeleteTransactions}
            disabled={loading}
            className="settings-button danger"
          >
            {loading ? "Processing..." : "Delete"}
          </button>
        </div>

        <div className="settings-option">
          <div className="option-info">
            <span className="settings-option-title">Reset Account</span>
            <p className="settings-option-subtitle">
              Delete all transactions AND remove the user account for a fresh start.
            </p>
          </div>
          <button
            onClick={handleResetAccount}
            disabled={loading}
            className="settings-button danger"
          >
            {loading ? "Processing..." : "Reset"}
          </button>
        </div>
      </div>

      {/* Application (Placeholder) */}
      <div className="settings-section">
        <h3>Application</h3>
        <div className="settings-option">
          <div className="option-info">
            <span className="settings-option-title">Uninstall</span>
            <p className="settings-option-subtitle">(Placeholder)</p>
          </div>
          <button className="settings-button danger" disabled>
            Uninstall
          </button>
        </div>
      </div>

      {/* Message display */}
      {message && <p className="settings-message">{message}</p>}
    </div>
  );
};

export default Settings;
