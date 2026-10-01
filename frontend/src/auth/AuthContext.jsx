import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../api/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('agrigraph_user');

      if (!saved || saved === 'null' || saved === 'undefined') {
        return null;
      }

      return JSON.parse(saved);
    } catch (error) {
      console.error('[AuthContext] Failed to parse agrigraph_user from localStorage:', error);
      try {
        localStorage.removeItem('agrigraph_user');
      } catch (removeError) {
        console.error('[AuthContext] Failed to clear invalid agrigraph_user:', removeError);
      }
      return null;
    }
  });

  const [token, setToken] = useState(() => {
    try {
      const savedToken = localStorage.getItem('agrigraph_token');

      if (!savedToken || savedToken === 'null' || savedToken === 'undefined') {
        return null;
      }

      return savedToken;
    } catch (error) {
      console.error('[AuthContext] Failed to read agrigraph_token from localStorage:', error);
      return null;
    }
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      authAPI
        .getMe()
        .then((res) => {
          if (res && res.data) {
            const loggedUser = res.data;
            setUser(loggedUser);
            try {
              localStorage.setItem('agrigraph_user', JSON.stringify(loggedUser));
            } catch (error) {
              console.error('[AuthContext] Failed to write user to localStorage:', error);
            }
          }
        })
        .catch((error) => {
          console.error('[AuthContext] Session validation failed:', error);
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

    if (!access_token || access_token === 'undefined') {
      throw new Error('Login failed: access token is missing');
    }

    setToken(access_token);
    setUser(loggedUser);

    try {
      localStorage.setItem('agrigraph_token', access_token);
      localStorage.setItem('agrigraph_user', JSON.stringify(loggedUser));
    } catch (error) {
      console.error('[AuthContext] Failed to save authentication to localStorage:', error);
    }

    return loggedUser;
  };

  const signup = async (userData) => {
    const res = await authAPI.signup(userData);
    const { access_token, user: newUser } = res.data;

    if (!access_token || access_token === 'undefined') {
      throw new Error('Signup failed: access token is missing');
    }

    setToken(access_token);
    setUser(newUser);

    try {
      localStorage.setItem('agrigraph_token', access_token);
      localStorage.setItem('agrigraph_user', JSON.stringify(newUser));
    } catch (error) {
      console.error('[AuthContext] Failed to save authentication to localStorage:', error);
    }

    return newUser;
  };

  const logout = () => {
    setUser(null);
    setToken(null);

    try {
      localStorage.removeItem('agrigraph_token');
      localStorage.removeItem('agrigraph_user');
    } catch (error) {
      console.error('[AuthContext] Failed to clear localStorage during logout:', error);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        signup,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
