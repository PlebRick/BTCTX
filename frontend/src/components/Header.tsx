// src/components/Header.tsx
import React from 'react';

interface HeaderProps {
  pageTitle: string;
}

const Header: React.FC<HeaderProps> = ({ pageTitle }) => {
  return (
    <header className="header">
      <div className="header-title">{pageTitle}</div>
      {/* If needed: right-side items here */}
    </header>
  );
};

export default Header;