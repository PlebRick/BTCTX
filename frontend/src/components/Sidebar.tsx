// src/components/Sidebar.tsx
import React from 'react';
import { NavLink } from 'react-router-dom';
import logo from '../assets/logo.svg';

const Sidebar: React.FC = () => {
  return (
    <aside className="sidebar">
      {/* Brand row */}
      <div className="sidebar-brand">
        <img src={logo} alt="BitcoinTX Logo" className="sidebar-logo" />
        <div className="sidebar-title">BitcoinTX</div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <NavLink to="/dashboard" className="nav-item">Dashboard</NavLink>
        <NavLink to="/transactions" className="nav-item">Transactions</NavLink>
        <NavLink to="/reports" className="nav-item">Reports</NavLink>
        <NavLink to="/settings" className="nav-item">Settings</NavLink>
      </nav>
    </aside>
  );
};

export default Sidebar;