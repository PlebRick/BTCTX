import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import '../styles/login.css';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false); // For toggling password visibility
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await axios.post('/api/login', { username, password }, { withCredentials: true });
      console.log(response.data);
      alert('Logged in successfully!');
      navigate('/dashboard');
    } catch (error) {
      console.error('Login error:', error);
      alert('Login failed. Please check your username/password or try again.');
    }
  };

  /** Toggle input type between 'password' and 'text' */
  const toggleShowPassword = () => {
    setShowPassword((prev) => !prev);
  };

  return (
    <div className="login-container">
      <div className="login-header">
        <img src="/icon.svg" alt="BitcoinTX Logo" className="login-logo" />
        <h1 className="login-title">Welcome to BitcoinTX</h1>
      </div>

      <div className="login-card">
        <h2 className="login-card-title">Sign In</h2>

        <form onSubmit={handleSubmit} className="login-form">
          {/* ---------- USERNAME FIELD ---------- */}
          <div className="login-form-group">
            <label htmlFor="username" className="login-label">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              className="login-input"
            />
          </div>

          {/* ---------- PASSWORD FIELD WITH 'SHOW PASSWORD' TEXT ABOVE THE LABEL ---------- */}
          <div className="login-form-group">
  {/* Row for label + show/hide link */}
  <div className="password-label-row">
    <label htmlFor="password" className="login-label">
      Password
    </label>
    <button
      type="button"
      className="toggle-password-btn"
      onClick={toggleShowPassword}
    >
      {showPassword ? 'Hide Password' : 'Show Password'}
    </button>
  </div>

  {/* Actual password input below */}
  <input
    id="password"
    type={showPassword ? 'text' : 'password'}
    value={password}
    onChange={e => setPassword(e.target.value)}
    required
    className="login-input"
  />
</div>

          <button type="submit" className="accent-btn login-btn">Log In</button>
        </form>

        <div className="login-create-account">
          <span className="create-account-text">Don’t have an account?</span>
          <a href="/register" className="create-account-link">Create Account</a>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
