// frontend/src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import TransactionPage from './pages/Transaction';

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        {/* Set TransactionPage as the default page for testing */}
        <Route path="/" element={<TransactionPage />} />
        <Route path="/transaction" element={<TransactionPage />} />
      </Routes>
    </Router>
  );
};

export default App;
