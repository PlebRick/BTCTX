import React from "react";
import "./styles/app.css"; // Ensures global + layout CSS is loaded
import { Routes, Route, Navigate } from "react-router-dom";

// Existing components
import AppLayout from "./components/AppLayout";
import Dashboard from "./pages/Dashboard";
import Transactions from "./pages/Transactions";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import TransactionForm from "./components/TransactionForm"; // The form

// New login & register pages
import LoginPage from "./pages/Login";
import RegisterPage from "./pages/Register";

const App: React.FC = () => {
  return (
    <Routes>
      {/* 
        Redirect the root URL ("/") to /dashboard by default.
        If you want unauthenticated users to land at /login instead,
        you can change this. 
      */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* Main app pages, each wrapped in AppLayout */}
      <Route
        path="/dashboard"
        element={
          <AppLayout>
            <Dashboard />
          </AppLayout>
        }
      />
      <Route
        path="/transactions"
        element={
          <AppLayout>
            <Transactions />
          </AppLayout>
        }
      />
      <Route
        path="/reports"
        element={
          <AppLayout>
            <Reports />
          </AppLayout>
        }
      />
      <Route
        path="/settings"
        element={
          <AppLayout>
            <Settings />
          </AppLayout>
        }
      />

      {/* Dedicated route to access the transaction form directly (for dev/testing) */}
      <Route path="/transactions/new" element={<TransactionForm />} />

      {/* -------------------------------------------------------------
         NEW ROUTES: Login & Register
         ------------------------------------------------------------- */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Fallback catch-all: back to dashboard if unknown route */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default App;