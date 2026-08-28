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

  if (isLoading) {
    return (
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
