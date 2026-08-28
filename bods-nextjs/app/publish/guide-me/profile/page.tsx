'use client';

/**
 * Redirects to the organisation profile page, matching Django's RedirectProfileView.
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';

export default function GuideMeProfileRedirectPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    if (user?.organisation_id) {
      router.replace(`/account/manage/org-profile/${user.organisation_id}`);
    } else {
      router.replace('/account');
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
