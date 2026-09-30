import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { Sprout, LogOut, User, ShieldCheck } from 'lucide-react';

export const Header = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header style={{
      backgroundColor: '#ffffff',
      borderBottom: '1px solid #e2e8f0',
      padding: '0.875rem 1.5rem',
      position: 'sticky',
      top: 0,
      zIndex: 40
    }}>
      <div style={{
        maxWidth: '1100px',
        margin: '0 auto',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        {/* Brand */}
        <Link to={user?.role === 'admin' ? '/admin' : '/farmer'} style={{
          textDecoration: 'none',
          display: 'flex',
          alignItems: 'center',
          gap: '0.625rem'
        }}>
          <div style={{
            backgroundColor: '#f0fdf4',
            color: '#15803d',
            padding: '0.5rem',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '1px solid #bbf7d0'
          }}>
            <Sprout size={24} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.25rem', fontWeight: '800', color: '#15803d', margin: 0, letterSpacing: '-0.02em' }}>
              AgriGraph
            </h1>
            <p style={{ fontSize: '0.75rem', color: '#64748b', margin: 0, fontWeight: '500' }}>
              {user?.role === 'admin' ? 'Knowledge Graph Administration' : 'Agricultural Knowledge Assistant'}
            </p>
          </div>
        </Link>

        {/* User Navigation / Actions */}
        {user ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {user.role === 'admin' && (
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.25rem',
                backgroundColor: '#eff6ff',
                color: '#1d4ed8',
                fontSize: '0.75rem',
                fontWeight: '600',
                padding: '0.25rem 0.625rem',
                borderRadius: '9999px',
                border: '1px solid #bfdbfe'
              }}>
                <ShieldCheck size={14} /> Admin Portal
              </span>
            )}

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                backgroundColor: '#e2e8f0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#475569'
              }}>
                <User size={16} />
              </div>
              <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#334155' }}>
                {user.name.split(' ')[0]}
              </span>
            </div>

            <button
              onClick={handleLogout}
              title="Logout"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.375rem',
                backgroundColor: '#f8fafc',
                border: '1px solid #cbd5e1',
                borderRadius: '8px',
                padding: '0.4rem 0.75rem',
                fontSize: '0.8125rem',
                fontWeight: '600',
                color: '#64748b'
              }}
              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#f1f5f9'; e.currentTarget.style.color = '#0f172a'; }}
              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#f8fafc'; e.currentTarget.style.color = '#64748b'; }}
            >
              <LogOut size={14} />
              Logout
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <Link to="/login" style={{
              textDecoration: 'none',
              color: '#15803d',
              fontWeight: '600',
              fontSize: '0.875rem',
              padding: '0.5rem 1rem'
            }}>
              Login
            </Link>
            <Link to="/signup" style={{
              textDecoration: 'none',
              backgroundColor: '#15803d',
              color: '#ffffff',
              fontWeight: '600',
              fontSize: '0.875rem',
              padding: '0.5rem 1rem',
              borderRadius: '8px'
            }}>
              Create Account
            </Link>
          </div>
        )}
      </div>
    </header>
  );
};
