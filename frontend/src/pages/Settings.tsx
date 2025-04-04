// FILE: frontend/src/pages/Settings.tsx

import React, { useState } from "react";
import api from "../api";
import "../styles/settings.css";

interface ApiErrorResponse {
  detail?: string;
}

const Settings: React.FC = () => {
  // -------------------------------------------
  // Existing state variables
  // -------------------------------------------
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  // -------------------------------------------
  // New: local states for credential form
  // -------------------------------------------
  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");

  // -------------------------------------------
  // Utility: Fetch current user ID
  // -------------------------------------------
  const getUserId = async (): Promise<number | null> => {
    try {
      // 🐛 Debug baseURL
    console.log("🔥 Axios baseURL:", api.defaults.baseURL);
    
      const res = await api.get("/users");
      const users = res.data as { id: number; username: string }[];
      return users.length > 0 ? users[0].id : null;
    } catch (err) {
      console.error("Failed to fetch user:", err);
      return null;
    }
  };

  // -------------------------------------------
  // Logout
  // -------------------------------------------
  const logoutAndRedirect = async () => {
    try {
      await api.post("/logout", {}, { withCredentials: true });
      window.location.href = "/login";
    } catch (err) {
      console.error("Logout failed:", err);
      setMessage("Failed to log out. Please try again.");
    }
  };

  const handleLogout = async () => {
    if (!window.confirm("Are you sure you want to log out?")) return;
    setLoading(true);
    setMessage("");
    await logoutAndRedirect();
    setLoading(false);
  };

  // -------------------------------------------
  // NEW: Replace handleResetCredentials with a form submission
  // -------------------------------------------
  const handleCredentialUpdate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      // Optional confirm (mimics your original message):
      if (
        !window.confirm(
          "This will reset your username and password, but keep existing transactions.\n\nContinue?"
        )
      ) {
        setLoading(false);
        return;
      }

      const userId = await getUserId();
      if (!userId) {
        setMessage("No user found to reset credentials.");
        return;
      }

      // Ensure at least one field is provided
      if (!newUsername && !newPassword) {
        setMessage("Please enter a new username or password (or both).");
        return;
      }

      // PATCH /users/{id} with new fields
      await api.patch(`/users/${userId}`, {
        username: newUsername || undefined,
        password: newPassword || undefined,
      });

      setMessage("Credentials updated successfully. Please log in again if required.");
      // Clear out fields
      setNewUsername("");
      setNewPassword("");
    } catch (error) {
      console.error("Error resetting credentials:", error);
      setMessage("Failed to reset credentials.");
    } finally {
      setLoading(false);
    }
  };

  // -------------------------------------------
  // Delete All Transactions
  // -------------------------------------------
  const handleDeleteTransactions = async () => {
    if (!window.confirm("Delete ALL transactions? This cannot be undone.")) return;
    setLoading(true);
    setMessage("");

    try {
      await api.delete<ApiErrorResponse>("/transactions/delete_all");
      setMessage("All transactions deleted.");
    } catch (error) {
      console.error("Error deleting transactions:", error);
      setMessage(error instanceof Error ? error.message : "Failed to delete transactions.");
    } finally {
      setLoading(false);
    }
  };

  // -------------------------------------------
  // Reset Account (delete user + transactions)
  // -------------------------------------------
  const handleResetAccount = async () => {
    const confirmMsg =
      "This will delete ALL transactions AND your user account.\n\nContinue? You’ll be redirected to /register after reset.";
    if (!window.confirm(confirmMsg)) return;

    setLoading(true);
    setMessage("");

    try {
      await api.post("/logout", {}, { withCredentials: true });
      await api.delete("/transactions/delete_all");
      const userId = await getUserId();
      if (userId) {
        await api.delete(`/users/${userId}`);
      }
      setMessage("Account reset. Redirecting to register...");
      window.location.href = "/register";
    } catch (error) {
      console.error("Reset account error:", error);
      setMessage("Failed to reset account. See console for details.");
    } finally {
      setLoading(false);
    }
  };

  // -------------------------------------------
  // Backup: Download
  // -------------------------------------------
  const handleDownloadBackup = async () => {
    const password = prompt("Enter a password to encrypt the backup:");
    if (!password) {
      setMessage("Backup canceled.");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const formData = new FormData();
      formData.append("password", password);

      const res = await api.post("/backup/download", formData, {
        responseType: "blob",
      });

      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "bitcoin_backup.btx");
      document.body.appendChild(link);
      link.click();
      link.remove();

      setMessage("Backup downloaded.");
    } catch (err) {
      console.error("Backup download failed:", err);
      setMessage("Failed to download backup.");
    } finally {
      setLoading(false);
    }
  };

  // -------------------------------------------
  // Backup: Restore
  // -------------------------------------------
  const handleRestoreBackup = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setMessage("");

    const formData = new FormData(event.currentTarget);
    const password = formData.get("password");
    const file = formData.get("file");

    if (!password || !(file instanceof File)) {
      setMessage("Please provide both a password and a file.");
      setLoading(false);
      return;
    }

    try {
      formData.set("file", file);
      const res = await api.post("/backup/restore", formData);
      setMessage(res.data.message || "Backup restored. Reloading...");
      setTimeout(() => window.location.reload(), 2000);
    } catch (err) {
      console.error("Restore failed:", err);
      setMessage("Failed to restore backup.");
    } finally {
      setLoading(false);
    }
  };

  // -------------------------------------------
  // Render
  // -------------------------------------------
  return (
    <div className="settings-container">
      <h2 className="settings-title">Settings</h2>

      {/* ------------------------------------------
          Account Section
      ------------------------------------------ */}
      <div className="settings-section">
        <h3>Account</h3>

        {/* Logout */}
        <div className="settings-option">
          <div className="option-info">
            <span className="settings-option-title">Logout</span>
            <p className="settings-option-subtitle">Sign out of your account.</p>
          </div>
          <button onClick={handleLogout} disabled={loading} className="settings-button">
            {loading ? "Processing..." : "Logout"}
          </button>
        </div>

        {/* Change Username & Password - now a form */}
        <div className="settings-option">
          <div className="option-info">
            <span className="settings-option-title">Reset Username &amp; Password</span>
            <p className="settings-option-subtitle">
              Change your username and password without deleting any transactions.
            </p>
          </div>

          <form onSubmit={handleCredentialUpdate} className="credential-update-form">
            <input
              type="text"
              placeholder="New Username"
              value={newUsername}
              onChange={(e) => setNewUsername(e.target.value)}
              style={{ marginRight: "0.5rem" }}
            />
            <input
              type="password"
              placeholder="New Password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              style={{ marginRight: "0.5rem" }}
            />

            <button type="submit" className="settings-button" disabled={loading}>
              {loading ? "Processing..." : "Update"}
            </button>
          </form>
        </div>
      </div>

      {/* ------------------------------------------
          Data Management Section
      ------------------------------------------ */}
      <div className="settings-section">
        <h3>Data Management</h3>

        {/* Delete All Transactions */}
        <div className="settings-option">
          <div className="option-info">
            <span className="settings-option-title">Delete All Transactions</span>
            <p className="settings-option-subtitle">
              Remove all transaction history. This action cannot be undone.
            </p>
          </div>
          <button onClick={handleDeleteTransactions} disabled={loading} className="settings-button danger">
            {loading ? "Processing..." : "Delete"}
          </button>
        </div>

        {/* Reset Account */}
        <div className="settings-option">
          <div className="option-info">
            <span className="settings-option-title">Reset Account</span>
            <p className="settings-option-subtitle">
              Delete all transactions AND remove the user account for a fresh start.
            </p>
          </div>
          <button onClick={handleResetAccount} disabled={loading} className="settings-button danger">
            {loading ? "Processing..." : "Reset"}
          </button>
        </div>
      </div>

      {/* ------------------------------------------
          Backup & Restore Section
      ------------------------------------------ */}
      <div className="settings-section">
        <h3>Backup & Restore</h3>
        <div className="settings-option">
          <div className="option-info">
            <span className="settings-option-title">Download Encrypted Backup</span>
            <p className="settings-option-subtitle">
              Save a secure backup of all app data (encrypted SQLite file).
            </p>
          </div>
          <button onClick={handleDownloadBackup} disabled={loading} className="settings-button">
            {loading ? "Processing..." : "Download"}
          </button>
        </div>

        <div className="settings-option">
          <form onSubmit={handleRestoreBackup} className="option-info" encType="multipart/form-data">
            <span className="settings-option-title">Restore from Backup</span>
            <p className="settings-option-subtitle">
              Upload a previously saved backup file and enter your password.
            </p>
            <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem" }}>
              <input type="file" name="file" accept=".btx" required style={{ color: "#fff", flex: "1" }} />
              <input
                type="password"
                name="password"
                placeholder="Password"
                required
                style={{ flex: "1", padding: "0.5rem" }}
              />
              <button type="submit" disabled={loading} className="settings-button" style={{ flexShrink: 0 }}>
                {loading ? "Processing..." : "Restore"}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* ------------------------------------------
          Application Section
      ------------------------------------------ */}
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
