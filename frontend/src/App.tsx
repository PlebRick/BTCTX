// src/App.tsx
import React from 'react';
import './styles/app.css';               // <-- ensures global + layout CSS is loaded
import { Routes, Route, Navigate } from 'react-router-dom';

import AppLayout from './components/AppLayout';
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import TransactionForm from './components/TransactionForm'; // the form

const App: React.FC = () => {
  return (
    <Routes>
      {/* Redirect the root URL ("/") to /dashboard */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* Main pages, each wrapped in layout */}
      <Route
        path="/dashboard"
        element={
          <AppLayout pageTitle="Dashboard">
            <Dashboard />
          </AppLayout>
        }
      />
      <Route
        path="/transactions"
        element={
          <AppLayout pageTitle="Transactions">
            <Transactions />
          </AppLayout>
        }
      />
      <Route
        path="/reports"
        element={
          <AppLayout pageTitle="Reports">
            <Reports />
          </AppLayout>
        }
      />
      <Route
        path="/settings"
        element={
          <AppLayout pageTitle="Settings">
            <Settings />
          </AppLayout>
        }
      />

      {/* Dedicated route to access TransactionForm directly (for dev/testing) */}
      <Route path="/transactions/new" element={<TransactionForm />} />

      {/* Fallback catch-all: back to dashboard if unknown route */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default App;