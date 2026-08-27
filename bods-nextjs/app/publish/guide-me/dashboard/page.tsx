'use client';

/**
 * Redirects to the publisher dashboard, matching Django's RedirectDashBoardView:
 * agents -> agent dashboard; single-org users -> their timetable list (feed-list default).
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';

export default function GuideMeDashboardRedirectPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    if (user?.is_agent_user) {
      router.replace('/publish/agent-dashboard');
    } else if (user?.organisation_id) {
      router.replace(`/publish/org/${user.organisation_id}/dataset/timetable`);
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
