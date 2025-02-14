// src/components/Sidebar.tsx
import React from 'react';
import { NavLink } from 'react-router-dom';

const Sidebar: React.FC = () => {
  return (
    <aside className="sidebar">
      {/* We'll use NavLink to get "active" styling if desired */}
      <NavLink to="/dashboard" className="nav-item">Dashboard</NavLink>
      <NavLink to="/transactions" className="nav-item">Transactions</NavLink>
      <NavLink to="/reports" className="nav-item">Reports</NavLink>
      <NavLink to="/settings" className="nav-item">Settings</NavLink>
    </aside>
  );
};

export default Sidebar;