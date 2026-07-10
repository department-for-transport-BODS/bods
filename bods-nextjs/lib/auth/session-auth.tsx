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
import { getCsrfToken } from '@/lib/api-client';
import type { User } from '@/types';

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

interface CsrfResponse {
  csrfToken: string;
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

async function fetchCsrfToken(): Promise<string> {
  const response = await fetch('/api/auth/csrf/', {
    method: 'GET',
    credentials: 'include',
    cache: 'no-store',
  });
  const data = (await response.json().catch(() => null)) as CsrfResponse | null;

  if (!response.ok || !data?.csrfToken) {
    throw new Error('Unable to initialise CSRF protection');
  }

  return data.csrfToken;
}

async function authRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<{ ok: boolean; status: number; data: T | null }> {
  const headers = new Headers(init.headers);
  const method = init.method?.toUpperCase() || 'GET';

  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method) && !headers.has('X-CSRFToken')) {
    headers.set('X-CSRFToken', getCsrfToken() || (await fetchCsrfToken()));
  }

  const response = await fetch(path, {
    ...init,
    headers,
    credentials: 'include',
    cache: 'no-store',
  });
  const data = (await response.json().catch(() => null)) as T | null;

  return { ok: response.ok, status: response.status, data };
}

async function fetchCurrentUser(): Promise<User | null> {
  const { ok, data } = await authRequest<Partial<User>>('/api/auth/user/');
  return ok && data ? normaliseUser(data) : null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const signOut = useCallback(async () => {
    try {
      await authRequest('/api/auth/logout/', { method: 'POST' });
    } finally {
      setUser(null);
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const { ok, data } = await authRequest<LoginResponse>('/api/auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!ok || !data) {
        throw new Error(getErrorMessage(data, 'Invalid email or password'));
      }

      const currentUser = data.user ? normaliseUser(data.user) : await fetchCurrentUser();
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

    Promise.all([fetchCsrfToken(), fetchCurrentUser()])
      .then(([, currentUser]) => {
        if (isMounted) setUser(currentUser);
      })
      .catch(() => {
        if (isMounted) setUser(null);
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      isLoading,
      login,
      signOut,
    }),
    [user, isLoading, login, signOut],
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
