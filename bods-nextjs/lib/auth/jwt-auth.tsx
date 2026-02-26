'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import type { User } from '@/types';
import { config } from '@/config';

const API_BASE_URL = config.djangoApiUrl;
const ACCESS_TOKEN_STORAGE_KEY = 'bods.auth.access';
const REFRESH_TOKEN_STORAGE_KEY = 'bods.auth.refresh';

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

interface LoginResponse {
  access?: string;
  refresh?: string;
  key?: string;
  token?: string;
  user?: Partial<User>;
  detail?: string;
  non_field_errors?: string[];
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function getErrorMessage(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== 'object') return fallback;
  if ('detail' in payload && typeof payload.detail === 'string') return payload.detail;
  if (
    'non_field_errors' in payload &&
    Array.isArray(payload.non_field_errors) &&
    typeof payload.non_field_errors[0] === 'string'
  ) {
    return payload.non_field_errors[0];
  }
  return fallback;
}

function readToken(key: string): string | null {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem(key);
}

function writeTokens(accessToken: string | null, refreshToken: string | null): void {
  if (typeof window === 'undefined') {
    return;
  }

  if (accessToken) {
    window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, accessToken);
  } else {
    window.localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
  }

  if (refreshToken) {
    window.localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, refreshToken);
  } else {
    window.localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY);
  }
}

function normaliseUser(user: Partial<User>): User {
  return {
    id: Number(user.id ?? 0),
    email: user.email || '',
    first_name: user.first_name,
    last_name: user.last_name,
    roles: user.roles,
    is_staff: user.is_staff,
    is_superuser: user.is_superuser,
  };
}

async function apiRequest<T>(
  path: string,
  init?: RequestInit,
  accessToken?: string
): Promise<{ ok: boolean; data: T | null }> {
  const headers = new Headers(init?.headers ?? undefined);
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  const data = (await response.json().catch(() => null)) as T | null;
  return { ok: response.ok, data };
}

async function fetchCurrentUser(accessToken: string): Promise<User> {
  const { ok, data } = await apiRequest<Partial<User>>('/api/auth/user/', { method: 'GET' }, accessToken);
  if (!ok || !data) {
    throw new Error('Could not fetch current user');
  }
  return normaliseUser(data);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const signOut = useCallback(async () => {
    const refreshToken = readToken(REFRESH_TOKEN_STORAGE_KEY);

    try {
      await apiRequest('/api/auth/logout/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(refreshToken ? { refresh: refreshToken } : {}),
      });
    } catch {
    }

    writeTokens(null, null);
    setUser(null);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const { ok, data } = await apiRequest<LoginResponse>('/api/auth/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!ok || !data) {
        throw new Error(getErrorMessage(data, 'Invalid email or password'));
      }

      const accessToken = data.access || data.key || data.token || null;
      const refreshToken = data.refresh || null;

      if (!accessToken) {
        throw new Error('Login succeeded but no access token was returned');
      }

      writeTokens(accessToken, refreshToken);

      if (data.user) {
        setUser(normaliseUser(data.user));
        return;
      }

      const currentUser = await fetchCurrentUser(accessToken);
      setUser(currentUser);
    } catch (error) {
      writeTokens(null, null);
      setUser(null);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;

    async function initialiseAuth() {
      const accessToken = readToken(ACCESS_TOKEN_STORAGE_KEY);

      if (!accessToken) {
        if (isMounted) {
          setIsLoading(false);
        }
        return;
      }

      try {
        const currentUser = await fetchCurrentUser(accessToken);

        if (isMounted) {
          setUser(currentUser);
        }
      } catch {
        writeTokens(null, null);

        if (isMounted) {
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    initialiseAuth();

    return () => {
      isMounted = false;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: !!user,
      isLoading,
      login,
      signOut,
    }),
    [user, isLoading, login, signOut]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}