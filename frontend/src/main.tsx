// frontend/src/main.tsx
import React from 'react';
import { createRoot } from 'react-dom/client';
import './styles/app.css'; // Ensure this path matches your CSS file location
import App from './App';

const rootElement = document.getElementById('root');
if (rootElement) {
  const root = createRoot(rootElement);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
