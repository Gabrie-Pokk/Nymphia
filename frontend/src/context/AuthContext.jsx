import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('nymphia_token'));
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('nymphia_user');
    return saved ? JSON.parse(saved) : null;
  });

  const login = (jwtToken, userData) => {
    setToken(jwtToken);
    setUser(userData);
    localStorage.setItem('nymphia_token', jwtToken);
    localStorage.setItem('nymphia_user', JSON.stringify(userData));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('nymphia_token');
    localStorage.removeItem('nymphia_user');
  };

  const updateUser = (fields) => {
    setUser((prev) => {
      const updated = { ...prev, ...fields };
      localStorage.setItem('nymphia_user', JSON.stringify(updated));
      return updated;
    });
  };

  const authHeaders = () => {
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  return (
    <AuthContext.Provider value={{ token, user, login, logout, updateUser, authHeaders, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
