import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('nymphia_token'));
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('nymphia_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [authMessage, setAuthMessage] = useState('');

  useEffect(() => {
    const handleAuthExpired = () => {
      setToken(null);
      setUser(null);
      localStorage.removeItem('nymphia_token');
      localStorage.removeItem('nymphia_user');
      setAuthMessage('Sua sessão expirou por segurança. Por favor, faça login novamente para continuar.');
    };

    window.addEventListener('nymphia:auth-expired', handleAuthExpired);
    return () => window.removeEventListener('nymphia:auth-expired', handleAuthExpired);
  }, []);

  const login = (jwtToken, userData) => {
    setToken(jwtToken);
    setUser(userData);
    setAuthMessage('');
    localStorage.setItem('nymphia_token', jwtToken);
    localStorage.setItem('nymphia_user', JSON.stringify(userData));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setAuthMessage('');
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
    <AuthContext.Provider
      value={{
        token,
        user,
        login,
        logout,
        updateUser,
        authHeaders,
        isAuthenticated: !!token,
        authMessage,
        clearAuthMessage: () => setAuthMessage('')
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
