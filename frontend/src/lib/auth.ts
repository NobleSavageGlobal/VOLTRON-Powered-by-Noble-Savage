import { authApi } from './api';
import type { User } from './types';

export function setTokens(accessToken: string, refreshToken: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }
}

export function clearTokens(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
}

export function getAccessToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('access_token');
  }
  return null;
}

export function isAuthenticated(): boolean {
  return getAccessToken() !== null;
}

export async function fetchCurrentUser(): Promise<User | null> {
  try {
    const resp = await authApi.me();
    return resp.data;
  } catch {
    return null;
  }
}
