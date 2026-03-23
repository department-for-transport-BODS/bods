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
import { getCsrfToken } from '@/lib/api-client';

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

interface LoginResponse {
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
): Promise<{ ok: boolean; status: number; data: T | null }> {
  const headers = new Headers(init?.headers ?? undefined);

  if (init?.method && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(init.method) && !headers.has('X-CSRFToken')) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      headers.set('X-CSRFToken', csrfToken);
    }
  }

  const response = await fetch(`${config.djangoApiUrl}${path}`, {
    ...init,
    headers,
    credentials: 'include',
  });

  const data = (await response.json().catch(() => null)) as T | null;
  return { ok: response.ok, status: response.status, data };
}

async function fetchCurrentUser(): Promise<User | null> {
  const { ok, data } = await apiRequest<Partial<User>>('/api/auth/user/', { method: 'GET' });
  if (!ok || !data) {
    return null;
  }
  return normaliseUser(data);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const signOut = useCallback(async () => {
    try {
      await apiRequest('/api/auth/logout/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
    } catch {
      // Sign out locally even if the server call fails
    }

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

      if (data.user) {
        setUser(normaliseUser(data.user));
        return;
      }

      const currentUser = await fetchCurrentUser();
      if (!currentUser) {
        throw new Error('Login succeeded but could not fetch user');
      }
      setUser(currentUser);
    } catch (error) {
      setUser(null);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;

    async function initialiseAuth() {
      try {
        const currentUser = await fetchCurrentUser();

        if (isMounted) {
          setUser(currentUser);
        }
      } catch {
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