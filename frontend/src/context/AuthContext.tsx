/**
 * Auth Context Provider
 * ======================
 * Manages authentication state across the application.
 * Provides login/logout functions and user profile data to all components.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { User, LoginRequest } from '../types';
import { authApi } from '../services/api';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * AuthProvider component that wraps the application and manages auth state.
 * Persists authentication state to localStorage for session continuity.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing session on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('sentinelai_user');
    const token = localStorage.getItem('sentinelai_access_token');
    if (storedUser && token) {
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        localStorage.removeItem('sentinelai_user');
        localStorage.removeItem('sentinelai_access_token');
      }
    }
    setIsLoading(false);
  }, []);

  /**
   * Authenticate user with credentials.
   * Stores tokens and user profile in localStorage on success.
   */
  const login = useCallback(async (data: LoginRequest) => {
    const response = await authApi.login(data);

    localStorage.setItem('sentinelai_access_token', response.access_token);
    localStorage.setItem('sentinelai_refresh_token', response.refresh_token);
    localStorage.setItem('sentinelai_user', JSON.stringify(response.user));

    setUser(response.user);
  }, []);

  /**
   * Log out the current user.
   * Clears all stored authentication data and resets state.
   */
  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignore logout API errors - clear local state regardless
    }
    localStorage.removeItem('sentinelai_access_token');
    localStorage.removeItem('sentinelai_refresh_token');
    localStorage.removeItem('sentinelai_user');
    setUser(null);
  }, []);

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to access the authentication context.
 * Must be used within an AuthProvider.
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
