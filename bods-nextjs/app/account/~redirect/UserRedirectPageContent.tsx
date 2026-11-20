'use client';

/**
 * Client-side equivalent of Django's UserRedirectView (`account/~redirect/`, the
 * LOGIN_REDIRECT_URL target): anonymous users are sent to sign in, signed-in users
 * are redirected to the home page of the host they are on. Django does not carry the
 * query string over (RedirectView.query_string is False), so neither do we.
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

function Redirect() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/');
  }, [router]);

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <p className="govuk-body">Redirecting...</p>
      </div>
    </div>
  );
}

export default function UserRedirectPage() {
  return (
    <ProtectedRoute>
      <Redirect />
    </ProtectedRoute>
  );
}
