// src/components/AppLayout.tsx
import React from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import Footer from './Footer';

interface LayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="app-layout">
      <Header />

      <div className="layout-body">
        <Sidebar />
        <main className="main-content">
          {children}
        </main>
      </div>

      <Footer />
    </div>
  );
};

export default AppLayout;