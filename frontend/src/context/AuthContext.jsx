import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const verifySession = async () => {
      const token = localStorage.getItem('feedbackpulse_token');
      if (token) {
        try {
          const userData = await api.getCurrentUser();
          setUser(userData);
        } catch (err) {
          console.error("Session verification failed:", err);
          localStorage.removeItem('feedbackpulse_token');
          setUser(null);
        }
      }
      setIsLoading(false);
    };
    verifySession();
  }, []);

  const login = async (email, password) => {
    try {
      const res = await api.login(email, password);
      localStorage.setItem('feedbackpulse_token', res.token);
      localStorage.setItem('feedbackpulse_user', JSON.stringify(res.user));
      localStorage.setItem('feedbackpulse_email', email);
      setUser(res.user);
      return res.user;
    } catch (err) {
      throw err;
    }
  };

  const signup = async (name, email, password) => {
    try {
      const res = await api.signup(name, email, password);
      localStorage.setItem('feedbackpulse_token', res.token);
      localStorage.setItem('feedbackpulse_user', JSON.stringify(res.user));
      localStorage.setItem('feedbackpulse_email', email);
      setUser(res.user);
      return res.user;
    } catch (err) {
      throw err;
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('feedbackpulse_token');
    localStorage.removeItem('feedbackpulse_user');
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
