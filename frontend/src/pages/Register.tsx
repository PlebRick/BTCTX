// frontend/src/pages/Register.tsx
import React, { useState } from 'react';
import axios from 'axios';

const RegisterPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const response = await axios.post(
        '/api/register',
        { username, password },
        { withCredentials: true } // if you want session cookies
      );
      console.log('Register response:', response.data);

      // Option A: auto-login next
      // const loginResponse = await axios.post('/api/login', { username, password }, { withCredentials: true });
      // console.log('Login response:', loginResponse.data);
      // navigate to dashboard or wherever

      // Option B: just show success and redirect to login page
      alert('Registration successful! Please log in.');
      // e.g. window.location.href = '/login';
    } catch (error) {
      console.error('Registration error:', error);
      alert('Failed to register. Try another username.');
    }
  };

  return (
    <div className="register-container">
      <h2>Create an Account</h2>
      <form onSubmit={handleRegister}>
        <div className="form-group">
          <label htmlFor="username">Username:</label>
          <input 
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required 
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password:</label>
          <input 
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required 
          />
        </div>
        <button type="submit">Register</button>
      </form>
    </div>
  );
};

export default RegisterPage;