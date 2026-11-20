/**
 * Protected Route Component
 *
 * Wraps pages that require authentication.
 * Redirects to login if not authenticated, preserving the intended destination.
 */

'use client';

import { useAuth } from '@/hooks/useAuth';
import { loginUrlWithNext } from '@/lib/auth/post-login-redirect';
import { useEffect, type ReactNode } from 'react';

interface ProtectedRouteProps {
  children: ReactNode;
  /**
   * Base login URL. Relative by default so sign-in stays on the current host.
   * A next= return URL is appended automatically.
   */
  redirectTo?: string;
}

export function ProtectedRoute({
  children,
  redirectTo = '/account/login',
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading || isAuthenticated) {
      return;
    }

    window.location.assign(loginUrlWithNext(redirectTo, window.location.href));
  }, [isAuthenticated, isLoading, redirectTo]);

  // Django resolves the session server-side, so the page simply appears (or
  // redirects). Render nothing while the session check is in flight; the layout's
  // header and footer stay in place.
  if (isLoading || !isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
