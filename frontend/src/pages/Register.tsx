// FILE: frontend/src/pages/Register.tsx

import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';
import '../styles/login.css'; // Reuse the same login styles

const RegisterPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await axios.post(
        '/api/users/register',
        { username, password },
        { withCredentials: true }
      );
      console.log('Register response:', response.data);
      alert('Registration successful! Please log in.');
      navigate('/login');
    } catch (error) {
      console.error('Registration error:', error);
      alert('Failed to register. If an account already exists, try logging in.');
    }
  };

  const toggleShowPassword = () => {
    setShowPassword(prev => !prev);
  };

  return (
    <div className="login-container">
      <div className="login-header">
        <img src="/icon.svg" alt="BitcoinTX Logo" className="login-logo" />
        <h1 className="login-title">Welcome to BitcoinTX</h1>
      </div>

      <div className="login-card">
        <h2 className="login-card-title">Create Account</h2>

        <form onSubmit={handleRegister} className="login-form">
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

          <div className="login-form-group">
            <div className="password-label-row">
              <label htmlFor="password" className="login-label">Password</label>
              <button
                type="button"
                className="toggle-password-btn"
                onClick={toggleShowPassword}
              >
                {showPassword ? 'Hide Password' : 'Show Password'}
              </button>
            </div>
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              className="login-input"
            />
          </div>

          <button type="submit" className="accent-btn login-btn">Register</button>
        </form>

        <div className="login-create-account">
          <span className="create-account-text">Already have an account?</span>
          <Link to="/login" className="create-account-link">Log In</Link>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
