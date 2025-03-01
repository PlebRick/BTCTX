// src/components/Sidebar.tsx
import React from 'react';
import { NavLink } from 'react-router-dom';
import logo from '../assets/logo.svg';
import Calculator from './Calculator';
import BtcConverter from './BtcConverter';

/**
 * Renders the top brand row of the sidebar,
 * including the site logo and the "BitcoinTX" title.
 */
const SidebarBrand: React.FC = () => {
  return (
    <div className="sidebar-brand">
      <img src={logo} alt="BitcoinTX Logo" className="sidebar-logo" />
      <div className="sidebar-title">BitcoinTX</div>
    </div>
  );
};

/**
 * Renders the main navigation links using NavLink:
 * - Dashboard
 * - Transactions
 * - Reports
 * - Settings
 * 
 * Class names are kept to preserve existing styling:
 *   .sidebar-nav, .nav-item
 */
const SidebarNav: React.FC = () => {
  return (
    <nav className="sidebar-nav">
      <NavLink to="/dashboard" className="nav-item">
        Dashboard
      </NavLink>
      <NavLink to="/transactions" className="nav-item">
        Transactions
      </NavLink>
      <NavLink to="/reports" className="nav-item">
        Reports
      </NavLink>
      <NavLink to="/settings" className="nav-item">
        Settings
      </NavLink>
    </nav>
  );
};

/**
 * SidebarTools
 * ------------
 * Stacks two tools vertically:
 *   1) BTC Converter (now on top)
 *   2) Calculator (below)
 * 
 * Class names:
 *   .sidebar-tools, .sidebar-converter, .sidebar-calculator
 * remain the same for consistency.
 */
const SidebarTools: React.FC = () => {
  return (
    <div className="sidebar-tools">
      <div className="sidebar-converter">
        <BtcConverter />
      </div>

      {/* Smaller calculator below */}
      <div className="sidebar-calculator">
        <Calculator />
      </div>
    </div>
  );
};

/**
 * The main exported Sidebar component composing:
 * 1) Brand/logo area
 * 2) Navigation links
 * 3) Tools (Converter + Calculator)
 * 
 * We keep <aside className="sidebar"> to preserve original styling.
 */
const Sidebar: React.FC = () => {
  return (
    <aside className="sidebar">
      {/* Brand row */}
      <SidebarBrand />

      {/* Navigation links */}
      <SidebarNav />

      {/* Tools (Converter on top, Calculator below) */}
      <SidebarTools />
    </aside>
  );
};

export default Sidebar;
