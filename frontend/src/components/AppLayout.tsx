// src/components/AppLayout.tsx
import React from 'react';
import Sidebar from './Sidebar';
import Header from './Header';

interface LayoutProps {
  pageTitle: string;         // The title to show in the Header
  children: React.ReactNode; // Page content
}

const AppLayout: React.FC<LayoutProps> = ({ pageTitle, children }) => {
  return (
    <div className="app-container">
      {/* Sidebar on the left, full height */}
      <Sidebar />

      {/* Content area on the right */}
      <div className="content-area">
        <Header pageTitle={pageTitle} />
        <main className="main-content">
          {children}
        </main>
      </div>
    </div>
  );
};

export default AppLayout;