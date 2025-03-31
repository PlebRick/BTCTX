// FILE: frontend/src/App.tsx

import React, { useEffect, useState, useCallback } from "react";
import "./styles/app.css";
import { Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";

import AppLayout from "./components/AppLayout";
import Dashboard from "./pages/Dashboard";
import Transactions from "./pages/Transactions";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import TransactionForm from "./components/TransactionForm";

import LoginPage from "./pages/Login";
import RegisterPage from "./pages/Register";

import api from "./api"; // Central Axios-based API client, sending cookies by default

// Loading spinner for a better UX vs. plain text
const LoadingSpinner: React.FC = () => (
  <div className="flex justify-center items-center mt-8">
    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-gray-900"></div>
  </div>
);

/**
 * PrivateRoute
 * -----------
 * - Checks user session by calling /api/protected (session-based auth).
 * - Shows a loading spinner while waiting.
 * - Redirects to /login if unauthorized.
 */
const PrivateRoute: React.FC<{ children: JSX.Element }> = ({ children }) => {
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    let isMounted = true;

    api
      .get("/protected", { withCredentials: true })
      .then(() => {
        if (isMounted) {
          setIsAuthenticated(true);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setIsAuthenticated(false);
          setLoading(false);
        }
        console.error("Authentication check failed:", err);
        // Production: send to monitoring (Sentry, etc.)
      });

    return () => {
      isMounted = false;
    };
  }, []);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

/**
 * App
 * ---
 * - On "/" or "/login", checks if any user exists to enforce single-user system:
 *   => If none, redirect to /register.
 * - Provides protected routes for Dashboard, Transactions, etc.
 * - Falls back to /dashboard if route not found.
 *
 * Production Best Practices (IRS Pub. 1075 context):
 * - Use secure cookies and https_only sessions (set in your backend).
 * - Possibly log auth events for compliance and auditing.
 * - Wrap repeated calls to /users/exists with memoization to reduce overhead.
 */
const App: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Tracks whether we've confirmed user existence
  const [checkedUserExists, setCheckedUserExists] = useState(false);
  // Prevent repeated calls if the user navigates quickly
  const [isChecking, setIsChecking] = useState(false);

  // Memoized function to check if a user exists
  const checkUserExists = useCallback(() => {
    if (isChecking) return;
    setIsChecking(true);

    api
      .get("/users/exists", { withCredentials: true })
      .then((res) => {
        setCheckedUserExists(true);
        if (!res.data.exists) {
          // If no user is found, we must register
          navigate("/register");
        }
      })
      .catch((err) => {
        console.error("Error checking user existence:", err);
        // Production: send to monitoring
        setCheckedUserExists(true);
      })
      .finally(() => setIsChecking(false));
  }, [isChecking, navigate]);

  useEffect(() => {
    // Only check user existence on certain paths
    if (["/", "/login"].includes(location.pathname)) {
      checkUserExists();
    } else {
      // In other routes, we can consider user existence 'checked'
      setCheckedUserExists(true);
    }
  }, [location.pathname, checkUserExists]);

  // Show spinner if we haven't confirmed user existence on relevant paths
  if (!checkedUserExists && ["/", "/login"].includes(location.pathname)) {
    return <LoadingSpinner />;
  }

  return (
    <Routes>
      {/* Default route redirects to /dashboard if user tries to go to '/' */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* PROTECTED ROUTES */}
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

      {/* PUBLIC ROUTES */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Fallback: go to dashboard for any unknown path */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default App;
