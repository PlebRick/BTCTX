import React, { useState } from 'react';
import axios from 'axios';

/**
 * A simple registration page for a single-user system.
 * 
 * Key points:
 *  - We call POST /api/users/register (which your FastAPI backend defines).
 *  - We include withCredentials: true to allow session cookies.
 *  - On success, we can either auto-login or redirect the user to a login page.
 */
const RegisterPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // Handle the form submission:
  // Prevent default submission, call the correct endpoint, handle success/errors.
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      // IMPORTANT: Use /api/users/register here.
      const response = await axios.post(
        '/api/users/register',
        { username, password },
        { withCredentials: true } // Required if your backend uses session cookies.
      );

      console.log('Register response:', response.data);

      // ------------------------------------------------------
      // Option A: Auto-login the newly created user
      // ------------------------------------------------------
      // If you want to automatically log them in after successful registration:
      /*
      const loginResponse = await axios.post(
        '/api/login',
        { username, password },
        { withCredentials: true }
      );
      console.log('Login response:', loginResponse.data);
      // Now that they're logged in, redirect to your main dashboard:
      window.location.href = '/dashboard';
      */

      // ------------------------------------------------------
      // Option B: Direct them to the login page
      // ------------------------------------------------------
      // If you'd rather not auto-login, just show a success message and redirect:
      alert('Registration successful! Please log in.');
      window.location.href = '/login';

    } catch (error) {
      console.error('Registration error:', error);
      // Provide a user-friendly alert or UI message
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
            onChange={e => setUsername(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="password">Password:</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
          />
        </div>

        <button type="submit">Register</button>
      </form>
    </div>
  );
};

export default RegisterPage;