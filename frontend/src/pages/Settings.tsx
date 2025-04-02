// FILE: frontend/src/pages/Settings.tsx

import React, { useState } from "react";
import api from "../api";
import "../styles/settings.css";

interface ApiErrorResponse {
  detail?: string;
}

const Settings: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const getUserId = async (): Promise<number | null> => {
    try {
      const res = await api.get("/users");
      const users = res.data as { id: number; username: string }[];
      return users.length > 0 ? users[0].id : null;
    } catch (err) {
      console.error("Failed to fetch user:", err);
      return null;
    }
  };

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

  const handleResetCredentials = async () => {
    const confirmMsg = "This will reset your username and password, but keep existing transactions.\n\nContinue?";
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

  const handleResetAccount = async () => {
    const confirmMsg = "This will delete ALL transactions AND your user account.\n\nContinue? You’ll be redirected to /register after reset.";
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

  return (
    <div className="settings-container">
      <h2 className="settings-title">Settings</h2>

      {/* Account Section */}
      <div className="settings-section">
        <h3>Account</h3>
        <div className="settings-option">
          <div className="option-info">
            <span className="settings-option-title">Logout</span>
            <p className="settings-option-subtitle">Sign out of your account.</p>
          </div>
          <button onClick={handleLogout} disabled={loading} className="settings-button">
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
          <button onClick={handleResetCredentials} disabled={loading} className="settings-button">
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
          <button onClick={handleDeleteTransactions} disabled={loading} className="settings-button danger">
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
          <button onClick={handleResetAccount} disabled={loading} className="settings-button danger">
            {loading ? "Processing..." : "Reset"}
          </button>
        </div>
      </div>

      {/* Backup & Restore Section */}
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
              <input type="password" name="password" placeholder="Password" required style={{ flex: "1", padding: "0.5rem" }} />
              <button type="submit" disabled={loading} className="settings-button" style={{ flexShrink: 0 }}>
                {loading ? "Processing..." : "Restore"}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Application Section */}
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
