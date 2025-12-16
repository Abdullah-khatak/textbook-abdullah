import React, { useState } from 'react';
import Layout from '@theme/Layout';
import styles from './signup.module.css';

export default function Signup() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    experienceLevel: 'beginner',
    softwareBackground: '',
    hardwareBackground: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/signup', {
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
        setError(data.detail || 'Signup failed. Please try again.');
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout title="Sign Up" description="Create your account">
      <div className={styles.signupContainer}>
        <div className={styles.signupCard}>
          <h1>Create Your Account</h1>
          <p className={styles.subtitle}>Join us to personalize your learning experience</p>

          {error && <div className={styles.error}>{error}</div>}

          <form onSubmit={handleSubmit} className={styles.form}>
            <div className={styles.formGroup}>
              <label>Name *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="Your full name"
              />
            </div>

            <div className={styles.formGroup}>
              <label>Email *</label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                placeholder="your@email.com"
              />
            </div>

            <div className={styles.formGroup}>
              <label>Password *</label>
              <input
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                placeholder="Create a strong password"
                minLength={8}
              />
            </div>

            <div className={styles.formGroup}>
              <label>Experience Level *</label>
              <select
                value={formData.experienceLevel}
                onChange={(e) => setFormData({...formData, experienceLevel: e.target.value})}
              >
                <option value="beginner">Beginner - New to robotics and AI</option>
                <option value="intermediate">Intermediate - Some programming experience</option>
                <option value="advanced">Advanced - Experienced with robotics/AI</option>
              </select>
            </div>

            <div className={styles.formGroup}>
              <label>Software Background</label>
              <textarea
                value={formData.softwareBackground}
                onChange={(e) => setFormData({...formData, softwareBackground: e.target.value})}
                placeholder="Tell us about your programming experience (Python, C++, JavaScript, etc.)"
                rows={3}
              />
              <small>This helps us personalize content for you</small>
            </div>

            <div className={styles.formGroup}>
              <label>Hardware Background</label>
              <textarea
                value={formData.hardwareBackground}
                onChange={(e) => setFormData({...formData, hardwareBackground: e.target.value})}
                placeholder="Tell us about your hardware experience (Arduino, Raspberry Pi, sensors, etc.)"
                rows={3}
              />
              <small>This helps us personalize content for you</small>
            </div>

            <button type="submit" className={styles.submitButton} disabled={loading}>
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          <p className={styles.signinLink}>
            Already have an account? <a href="/signin">Sign In</a>
          </p>
        </div>
      </div>
    </Layout>
  );
}