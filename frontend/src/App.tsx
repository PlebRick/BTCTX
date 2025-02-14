// src/App.tsx
import React from 'react';
import './styles/app.css';  // global theme + layout
import { Routes, Route, Navigate } from 'react-router-dom';

import AppLayout from './components/AppLayout';
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import Reports from './pages/Reports';
import Settings from './pages/Settings';

const App: React.FC = () => {
  return (
    <Routes>
      {/* Redirect root to /dashboard */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

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
    </Routes>
  );
};

export default App;