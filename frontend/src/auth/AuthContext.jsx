import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../api/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('agrigraph_user');

    if (!saved || saved === 'undefined' || saved === 'null') {
      return null;
    }

    try {
      return JSON.parse(saved);
    } catch (error) {
      localStorage.removeItem('agrigraph_user');
      return null;
    }
  });

  const [token, setToken] = useState(() => {
    const savedToken = localStorage.getItem('agrigraph_token');

    if (!savedToken || savedToken === 'undefined' || savedToken === 'null') {
      return null;
    }

    return savedToken;
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      authAPI.getMe()
        .then((res) => {
          const loggedUser = res.data;

          setUser(loggedUser);
          localStorage.setItem(
            'agrigraph_user',
            JSON.stringify(loggedUser)
          );
        })
        .catch(() => {
          logout();
        })
        .finally(() => {
          setLoading(false);
        });
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

    localStorage.setItem('agrigraph_token', access_token);
    localStorage.setItem(
      'agrigraph_user',
      JSON.stringify(loggedUser)
    );

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

    localStorage.setItem('agrigraph_token', access_token);
    localStorage.setItem(
      'agrigraph_user',
      JSON.stringify(newUser)
    );

    return newUser;
  };

  const logout = () => {
    setUser(null);
    setToken(null);

    localStorage.removeItem('agrigraph_token');
    localStorage.removeItem('agrigraph_user');
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
