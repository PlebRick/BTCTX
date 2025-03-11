// frontend/src/pages/Login.tsx
import React, { useState } from 'react';
import axios from 'axios';
import '../styles/login.css';  // or wherever you keep this page’s CSS

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Send credentials to /api/login with the session cookie
      const response = await axios.post(
        '/api/login',
        { username, password },
        { withCredentials: true }
      );

      console.log(response.data);
      alert('Logged in successfully!');
      // TODO: navigate to a protected page (e.g., /dashboard) here
    } catch (error) {
      console.error('Login error:', error);
      alert('Login failed');
    }
  };

  return (
    <div className="login-container">
      <div className="login-header">
        {/* Replace with your actual logo image path if needed */}
        <img src="/icon.svg" alt="BitcoinTX Logo" className="login-logo" />
        <h1 className="login-title">Welcome to BitcoinTX</h1>
      </div>

      <div className="login-card">
        <h2 className="login-card-title">Sign In</h2>
        <form onSubmit={handleSubmit} className="login-form">
          <div className="login-form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
            />
          </div>

          <div className="login-form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="accent-btn login-btn">
            Log In
          </button>
        </form>

        <div className="login-create-account">
          <span>Don’t have an account?</span>
          <a href="/register" className="create-account-link">
            Create Account
          </a>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;