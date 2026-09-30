import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from './AuthContext';

export const ProtectedRoute = ({ allowedRole }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <p style={{ fontSize: '1.25rem', color: '#15803d', fontWeight: '600' }}>🌱 Loading AgriGraph...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRole && user.role !== allowedRole) {
    // Redirect unauthorized access to appropriate portal
    return <Navigate to={user.role === 'admin' ? '/admin' : '/farmer'} replace />;
  }

  return <Outlet />;
};
