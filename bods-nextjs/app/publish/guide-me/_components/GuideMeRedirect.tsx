'use client';

/**
 * Client-side equivalent of Django's guide-me Redirect*View classes: work out a
 * destination from the signed-in user, then replace the current history entry.
 *
 * Destinations are public paths (no /publish prefix); the proxy maps them onto
 * the internal route for the publish host.
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useAuth } from '@/hooks/useAuth';
import type { User } from '@/types';

export type DestinationFor = (user: User) => string;

function Redirect({ destinationFor }: { destinationFor: DestinationFor }) {
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!user) {
      return;
    }

    router.replace(destinationFor(user));
  }, [user, router, destinationFor]);

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <p className="govuk-body">Redirecting...</p>
      </div>
    </div>
  );
}

export function GuideMeRedirect({ destinationFor }: { destinationFor: DestinationFor }) {
  return (
    <ProtectedRoute>
      <Redirect destinationFor={destinationFor} />
    </ProtectedRoute>
  );
}
