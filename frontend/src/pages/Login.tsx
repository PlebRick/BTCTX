// frontend/src/pages/Login.tsx
import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';  // Import from react-router-dom
import '../styles/login.css';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  
  // useNavigate hook for client-side transitions without reload
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Send credentials to /api/login with session cookie
      const response = await axios.post(
        '/api/login',
        { username, password },
        { withCredentials: true }
      );

      // If successful, the backend sets the session; we can log response data if needed
      console.log(response.data);
      
      // Notify user, then redirect
      alert('Logged in successfully!');
      navigate('/dashboard');

    } catch (error) {
      console.error('Login error:', error);
      // If password invalid or user not found, the backend likely returns 401
      alert('Login failed. Please check your username/password or try again.');
    }
  };

  return (
    <div className="login-container">
      <div className="login-header">
        {/* Optionally replace with your actual logo path */}
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
