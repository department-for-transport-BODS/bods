'use client';

/**
 * Redirects to the signed-in admin's own organisation invite page, matching
 * Django's users:invite view (which resolves the organisation implicitly from
 * request.user rather than a URL parameter).
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';

export default function AccountManageInviteRedirectPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    if (user?.organisation_id) {
      router.replace(`/publish/org/${user.organisation_id}/manage/invite`);
    } else {
      router.replace('/publish/account');
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
