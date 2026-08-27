'use client';

/**
 * Redirects to the "start publishing" flow, matching Django's RedirectPublishView:
 * agents -> select organisation; single-org users -> choose data type.
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';

export default function GuideMePublishRedirectPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    if (user?.is_agent_user) {
      router.replace('/publish/org');
    } else if (user?.organisation_id) {
      router.replace(`/publish/org/${user.organisation_id}/dataset`);
    } else {
      router.replace('/publish/org');
    }
  }, [isLoading, user, router]);

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <p className="govuk-body">Redirecting...</p>
      </div>
    </div>
  );
}
