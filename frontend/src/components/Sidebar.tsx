// src/components/Sidebar.tsx
import React from 'react';
import { NavLink } from 'react-router-dom';
import logo from '../assets/logo.svg'; // adjust path if needed

const Sidebar: React.FC = () => {
  return (
    <aside className="sidebar">
      {/* Top Brand Area */}
      <div className="sidebar-brand">
        <img src={logo} alt="BitcoinTX Logo" className="sidebar-logo" />
        <div className="sidebar-title">BitcoinTX</div>
      </div>

      {/* Subtle divider line */}
      <hr className="sidebar-divider" />

      {/* Navigation Links */}
      <nav className="sidebar-nav">
        <NavLink to="/dashboard" className="nav-item">Dashboard</NavLink>
        <NavLink to="/transactions" className="nav-item">Transactions</NavLink>
        <NavLink to="/reports" className="nav-item">Reports</NavLink>
        <NavLink to="/settings" className="nav-item">Settings</NavLink>
      </nav>

      {/* Button at bottom */}
      <button className="btn sidebar-btn">Add Transaction</button>
      {/* Or "Add Transaction," if that’s your preference */}
    </aside>
  );
};

export default Sidebar;