// FILE: frontend/src/App.tsx

import React, { useEffect, useState } from "react";
import "./styles/app.css";
import { Routes, Route, Navigate } from "react-router-dom";

import AppLayout from "./components/AppLayout";
import Dashboard from "./pages/Dashboard";
import Transactions from "./pages/Transactions";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import TransactionForm from "./components/TransactionForm";

import LoginPage from "./pages/Login";
import RegisterPage from "./pages/Register";

import api from "./api"; // Axios-based client with credentials

/**
 * Simple loading spinner for improved UX.
 * You can style it with Tailwind (if in use) or your own CSS.
 */
const LoadingSpinner: React.FC = () => (
  <div className="flex justify-center items-center mt-8">
    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-gray-900"></div>
  </div>
);

/**
 * PrivateRoute
 * -----------
 * Checks user session by calling /api/protected (session-based auth).
 * - If authenticated, show the child route.
 * - If not, redirect to /login.
 * Shows a loading spinner while waiting.
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
          console.error("Authentication check failed:", err);
          setIsAuthenticated(false);
          setLoading(false);
        }
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
 * - '/' redirects to '/dashboard' if you're authenticated, or
 *   to '/login' if not (handled by PrivateRoute).
 * - Protected routes require PrivateRoute.
 * - Login and Register are public routes.
 * - Fallback route also goes to '/dashboard'.
 */
const App: React.FC = () => {
  return (
    <Routes>
      {/* Default route: go to dashboard (PrivateRoute will handle auth check) */}
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

      {/* Fallback route → go to dashboard (requires auth) */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default App;
