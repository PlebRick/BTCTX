// src/components/Sidebar.tsx
import React from 'react';
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
 * SidebarTools
 * ------------
 * Displays:
 *   1) BTC Converter (top)
 *   2) Calculator (below)
 */
const SidebarTools: React.FC = () => {
  return (
    <div className="sidebar-tools">
      <div className="sidebar-converter">
        <BtcConverter />
      </div>

      <div className="sidebar-calculator">
        <Calculator />
      </div>
    </div>
  );
};

/**
 * The main Sidebar component:
 *  - Brand (logo + title)
 *  - Tools (Converter + Calculator)
 * 
 * No nav links here, as they've been moved to the header.
 */
const Sidebar: React.FC = () => {
  return (
    <aside className="sidebar">
      {/* Brand row */}
      <SidebarBrand />

      {/* Tools (Converter + Calculator) */}
      <SidebarTools />
    </aside>
  );
};

export default Sidebar;
