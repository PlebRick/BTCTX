import React from 'react';
import { NavLink } from 'react-router-dom';

interface HeaderProps {
  pageTitle?: string; // optional if you like
}

const Header: React.FC<HeaderProps> = ({ pageTitle }) => {
  return (
    <header className="header">
      {/* If pageTitle is provided, render it */}
      {pageTitle && <h1>{pageTitle}</h1>}

      <nav className="header-nav">
        <NavLink
          to="/dashboard"
          className={({ isActive }) =>
            isActive ? 'header-nav-item active' : 'header-nav-item'
          }
        >
          Dashboard
        </NavLink>
        <NavLink
          to="/transactions"
          className={({ isActive }) =>
            isActive ? 'header-nav-item active' : 'header-nav-item'
          }
        >
          Transactions
        </NavLink>
        <NavLink
          to="/reports"
          className={({ isActive }) =>
            isActive ? 'header-nav-item active' : 'header-nav-item'
          }
        >
          Reports
        </NavLink>
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            isActive ? 'header-nav-item active' : 'header-nav-item'
          }
        >
          Settings
        </NavLink>
      </nav>
    </header>
  );
};

export default Header;
