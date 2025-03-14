//frontend/src/App.tsx
import React, { useEffect, useState } from "react";
import "./styles/app.css"; // Ensures global + layout CSS is loaded
import { Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";

import AppLayout from "./components/AppLayout";
import Dashboard from "./pages/Dashboard";
import Transactions from "./pages/Transactions";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import TransactionForm from "./components/TransactionForm";

import LoginPage from "./pages/Login";
import RegisterPage from "./pages/Register";

/**
 * PrivateRoute component:
 * 1. Checks if the user is authenticated by calling a protected endpoint.
 * 2. While loading, shows a "Checking auth..." message.
 * 3. If not authenticated, redirects to /login.
 * 4. Otherwise, renders the children (protected component).
 */
const PrivateRoute: React.FC<{ children: JSX.Element }> = ({ children }) => {
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check session status by hitting a protected route
    axios
      .get("/api/protected", { withCredentials: true })
      .then(() => {
        setIsAuthenticated(true);
        setLoading(false);
      })
      .catch(() => {
        setIsAuthenticated(false);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div style={{ textAlign: "center", marginTop: "2rem" }}>Checking auth...</div>;
  }

  if (!isAuthenticated) {
    // Not logged in => redirect to /login
    return <Navigate to="/login" replace />;
  }

  // Authenticated => render the intended page
  return children;
};

const App: React.FC = () => {
  return (
    <Routes>
      {/*
        Redirect root URL ("/") to /dashboard by default.
        But if user isn't logged in, PrivateRoute will bounce them to /login.
      */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* PROTECTED ROUTES: wrapped in PrivateRoute */}
      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <AppLayout>
              <Dashboard />
            </AppLayout>
          </PrivateRoute>
        }
      />
      <Route
        path="/transactions"
        element={
          <PrivateRoute>
            <AppLayout>
              <Transactions />
            </AppLayout>
          </PrivateRoute>
        }
      />
      <Route
        path="/transactions/new"
        element={
          <PrivateRoute>
            <TransactionForm />
          </PrivateRoute>
        }
      />
      <Route
        path="/reports"
        element={
          <PrivateRoute>
            <AppLayout>
              <Reports />
            </AppLayout>
          </PrivateRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <PrivateRoute>
            <AppLayout>
              <Settings />
            </AppLayout>
          </PrivateRoute>
        }
      />

      {/* PUBLIC ROUTES: Login & Register */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Fallback catch-all: back to /dashboard (which is also protected) */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default App;