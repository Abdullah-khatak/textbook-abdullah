import React, { useState } from 'react';
import Layout from '@theme/Layout';
import styles from './signup.module.css';

export default function Signin() {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/signin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Save user profile to localStorage
        localStorage.setItem('userProfile', JSON.stringify(data.user));
        localStorage.setItem('isLoggedIn', 'true');

        // Redirect to intro page
        window.location.href = '/docs/intro';
      } else {
        setError(data.detail || 'Invalid email or password.');
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout title="Sign In" description="Sign in to your account">
      <div className={styles.signupContainer}>
        <div className={styles.signupCard}>
          <h1>Welcome Back</h1>
          <p className={styles.subtitle}>Sign in to continue your learning journey</p>

          {error && <div className={styles.error}>{error}</div>}

          <form onSubmit={handleSubmit} className={styles.form}>
            <div className={styles.formGroup}>
              <label>Email</label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                placeholder="your@email.com"
              />
            </div>

            <div className={styles.formGroup}>
              <label>Password</label>
              <input
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                placeholder="Your password"
              />
            </div>

            <button type="submit" className={styles.submitButton} disabled={loading}>
              {loading ? 'Signing In...' : 'Sign In'}
            </button>
          </form>

          <p className={styles.signinLink}>
            Don't have an account? <a href="/signup">Sign Up</a>
          </p>
        </div>
      </div>
    </Layout>
  );
}