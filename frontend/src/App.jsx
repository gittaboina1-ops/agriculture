import React from 'react';
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate
} from 'react-router-dom';

import { AuthProvider } from './auth/AuthContext';
import { ProtectedRoute } from './auth/ProtectedRoute';

import { Login } from './pages/Login';
import { Signup } from './pages/Signup';

import { FarmerHome } from './pages/FarmerHome';

import { AdminHome } from './pages/AdminHome';
import { AdminUpload } from './pages/AdminUpload';
import { AdminGraph } from './pages/AdminGraph';
import { AdminSources } from './pages/AdminSources';
import { AdminConflicts } from './pages/AdminConflicts';
import { AdminDataQuality } from './pages/AdminDataQuality';

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>

          <Route
            path="/login"
            element={<Login />}
          />

          <Route
            path="/signup"
            element={<Signup />}
          />

          <Route
            element={
              <ProtectedRoute allowedRole="farmer" />
            }
          >
            <Route
              path="/farmer"
              element={<FarmerHome />}
            />
          </Route>

          <Route
            element={
              <ProtectedRoute allowedRole="admin" />
            }
          >
            <Route
              path="/admin"
              element={<AdminHome />}
            />

            <Route
              path="/admin/upload"
              element={<AdminUpload />}
            />

            <Route
              path="/admin/graph"
              element={<AdminGraph />}
            />

            <Route
              path="/admin/sources"
              element={<AdminSources />}
            />

            <Route
              path="/admin/conflicts"
              element={<AdminConflicts />}
            />

            <Route
              path="/admin/validation"
              element={<AdminDataQuality />}
            />
          </Route>

          <Route
            path="/"
            element={
              <Navigate
                to="/login"
                replace
              />
            }
          />

          <Route
            path="*"
            element={
              <Navigate
                to="/login"
                replace
              />
            }
          />

        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
