import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../api/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('agrigraph_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('agrigraph_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Validate session on mount if token exists
    if (token) {
      authAPI.getMe()
        .then((res) => {
          setUser(res.data);
          localStorage.setItem('agrigraph_user', JSON.stringify(res.data));
        })
        .catch(() => {
          logout();
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (email, password) => {
    const res = await authAPI.login(email, password);
    const { access_token, user: loggedUser } = res.data;
    setToken(access_token);
    setUser(loggedUser);
    localStorage.setItem('agrigraph_token', access_token);
    localStorage.setItem('agrigraph_user', JSON.stringify(loggedUser));
    return loggedUser;
  };

  const signup = async (userData) => {
    const res = await authAPI.signup(userData);
    const { access_token, user: newUser } = res.data;
    setToken(access_token);
    setUser(newUser);
    localStorage.setItem('agrigraph_token', access_token);
    localStorage.setItem('agrigraph_user', JSON.stringify(newUser));
    return newUser;
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('agrigraph_token');
    localStorage.removeItem('agrigraph_user');
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
