// src/components/Header.tsx
import React from 'react';

const Header: React.FC = () => {
  return (
    <header className="header">
      <div className="brand">BitcoinTX</div>
      {/* You could add a user profile, search, or other controls on the right */}
    </header>
  );
};

export default Header;