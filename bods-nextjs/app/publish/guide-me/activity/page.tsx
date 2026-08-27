'use client';

/**
 * Redirects to consumer activity stats, matching Django's RedirectDataActivityView:
 * agents -> agent dashboard (Django deep-links a "next=data-activity" param there;
 * our agent dashboard doesn't support that yet, so agents land on the dashboard itself);
 * single-org users -> their organisation's data activity page.
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';

export default function GuideMeActivityRedirectPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    if (user?.is_agent_user) {
      router.replace('/publish/agent-dashboard');
    } else if (user?.organisation_id) {
      router.replace(`/publish/org/${user.organisation_id}/dataset/data-activity?prev=guide-me`);
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
