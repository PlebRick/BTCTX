// src/components/Sidebar.tsx
import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import logo from '../assets/logo.svg';

const Sidebar: React.FC = () => {
  const location = useLocation();

  // Decide the button label & placeholder action
  let buttonLabel = '';
  let buttonAction = () => {}; // no-op placeholder

  switch (location.pathname) {
    case '/dashboard':
    case '/transactions':
      buttonLabel = 'Add Transaction';
      buttonAction = () => {
        console.log('TODO: Show Add Transaction Form');
      };
      break;

    case '/reports':
      buttonLabel = 'Generate Report';
      buttonAction = () => {
        console.log('TODO: Generate Report');
      };
      break;

    case '/settings':
      buttonLabel = 'Logout';
      buttonAction = () => {
        console.log('TODO: Handle Logout');
      };
      break;

    default:
      // For any other route, you could hide the button or set a default label
      buttonLabel = '';
      break;
  }

  return (
    <aside className="sidebar">
      {/* Brand row */}
      <div className="sidebar-brand">
        <img src={logo} alt="BitcoinTX Logo" className="sidebar-logo" />
        <div className="sidebar-title">BitcoinTX</div>
      </div>

      {/* Nav divider line (if using <hr className="sidebar-divider" />) 
          <hr className="sidebar-divider" /> 
      */}

      {/* Navigation */}
      <nav className="sidebar-nav">
        <NavLink to="/dashboard" className="nav-item">Dashboard</NavLink>
        <NavLink to="/transactions" className="nav-item">Transactions</NavLink>
        <NavLink to="/reports" className="nav-item">Reports</NavLink>
        <NavLink to="/settings" className="nav-item">Settings</NavLink>
      </nav>

      {/* Conditionally render the button if there's a label */}
      {buttonLabel && (
        <button
          className="btn sidebar-btn"
          onClick={buttonAction}
        >
          {buttonLabel}
        </button>
      )}
    </aside>
  );
};

export default Sidebar;