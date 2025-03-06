import React from 'react';
import { NavLink } from 'react-router-dom';

const Header: React.FC = () => {
  return (
    <header className="header">
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
