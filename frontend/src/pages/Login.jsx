import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { Sprout, Lock, Mail, AlertCircle, CheckCircle2 } from 'lucide-react';

export const Login = () => {
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [message] = useState(location.state?.message || '');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const user = await login(email.trim().toLowerCase(), password);
      if (user.role === 'admin') {
        navigate('/admin');
      } else {
        navigate('/farmer');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemoLogin = (role) => {
    if (role === 'farmer') {
      setEmail('farmer@agrigraph.org');
      setPassword('farmerpassword123');
    } else {
      setEmail('vundhyalaakeshreddy@gmail.com');
      setPassword('reddy@123');
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#f8fafc',
      padding: '1.5rem'
    }}>
      <div style={{
        maxWidth: '440px',
        width: '100%',
        backgroundColor: '#ffffff',
        borderRadius: '20px',
        padding: '2.5rem 2rem',
        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.03)',
        border: '1px solid #e2e8f0'
      }}>
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{
            display: 'inline-flex',
            backgroundColor: '#f0fdf4',
            color: '#15803d',
            padding: '0.875rem',
            borderRadius: '16px',
            border: '1px solid #bbf7d0',
            marginBottom: '1rem'
          }}>
            <Sprout size={36} />
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: '800', color: '#15803d', margin: 0, letterSpacing: '-0.02em' }}>
            AgriGraph
          </h1>
          <p style={{ fontSize: '0.9375rem', color: '#64748b', marginTop: '0.25rem', fontWeight: '500' }}>
            Welcome back to your agricultural assistant
          </p>
        </div>

        {message && (
          <div style={{
            backgroundColor: '#f0fdf4',
            border: '1px solid #bbf7d0',
            color: '#15803d',
            padding: '0.75rem 1rem',
            borderRadius: '10px',
            fontSize: '0.875rem',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <CheckCircle2 size={18} />
            <span>{message}</span>
          </div>
        )}

        {error && (
          <div style={{
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            color: '#b91c1c',
            padding: '0.75rem 1rem',
            borderRadius: '10px',
            fontSize: '0.875rem',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '700', color: '#334155', marginBottom: '0.5rem' }}>
              Email Address
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                style={{
                  width: '100%',
                  padding: '0.875rem 1rem 0.875rem 2.5rem',
                  fontSize: '1rem',
                  border: '1px solid #cbd5e1',
                  borderRadius: '10px',
                  outline: 'none',
                  backgroundColor: '#f8fafc'
                }}
                onFocus={(e) => { e.target.style.borderColor = '#15803d'; e.target.style.backgroundColor = '#ffffff'; }}
                onBlur={(e) => { e.target.style.borderColor = '#cbd5e1'; }}
              />
              <Mail size={18} color="#94a3b8" style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)' }} />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '700', color: '#334155', marginBottom: '0.5rem' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                style={{
                  width: '100%',
                  padding: '0.875rem 1rem 0.875rem 2.5rem',
                  fontSize: '1rem',
                  border: '1px solid #cbd5e1',
                  borderRadius: '10px',
                  outline: 'none',
                  backgroundColor: '#f8fafc'
                }}
                onFocus={(e) => { e.target.style.borderColor = '#15803d'; e.target.style.backgroundColor = '#ffffff'; }}
                onBlur={(e) => { e.target.style.borderColor = '#cbd5e1'; }}
              />
              <Lock size={18} color="#94a3b8" style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)' }} />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              marginTop: '0.5rem',
              backgroundColor: '#15803d',
              color: '#ffffff',
              border: 'none',
              padding: '0.9375rem',
              borderRadius: '12px',
              fontSize: '1.0625rem',
              fontWeight: '800',
              cursor: loading ? 'wait' : 'pointer',
              boxShadow: '0 4px 6px -1px rgba(21, 128, 61, 0.25)'
            }}
            onMouseEnter={(e) => { if (!loading) e.currentTarget.style.backgroundColor = '#166534'; }}
            onMouseLeave={(e) => { if (!loading) e.currentTarget.style.backgroundColor = '#15803d'; }}
          >
            {loading ? 'Logging In...' : 'Login'}
          </button>
        </form>

        {/* Evaluation Quick Fill Buttons */}
        <div style={{
          marginTop: '1.5rem',
          padding: '1rem',
          backgroundColor: '#f0fdf4',
          borderRadius: '12px',
          border: '1px solid #bbf7d0',
          textAlign: 'center'
        }}>
          <p style={{ fontSize: '0.8125rem', color: '#166534', fontWeight: '700', marginBottom: '0.5rem' }}>
            Quick Logins (Hackathon Evaluation):
          </p>
          <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
            
          
          </div>
        </div>

        <div style={{ textAlign: 'center', marginTop: '1.5rem' }}>
          <p style={{ fontSize: '0.875rem', color: '#64748b' }}>
            New farmer?{' '}
            <Link to="/signup" style={{ color: '#15803d', fontWeight: '700', textDecoration: 'none' }}>
              Create Farmer Account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};
