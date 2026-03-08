'use client';

import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { authApi } from '@/lib/api';
import { clearTokens, setTokens } from '@/lib/auth';
import type { User } from '@/lib/types';

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    email: string;
    password: string;
    full_name: string;
    org_name?: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token =
      typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (!token) {
      setIsLoading(false);
      return;
    }
    authApi
      .me()
      .then((resp) => setUser(resp.data))
      .catch(() => clearTokens())
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const resp = await authApi.login({ email, password });
    setTokens(resp.data.access_token, resp.data.refresh_token);
    const meResp = await authApi.me();
    setUser(meResp.data);
  }, []);

  const register = useCallback(
    async (data: {
      email: string;
      password: string;
      full_name: string;
      org_name?: string;
    }) => {
      await authApi.register(data);
      await login(data.email, data.password);
    },
    [login]
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      clearTokens();
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
