'use client';

/**
 * Org admin: resend a pending standard (non-agent) invite.
 */

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { HOSTS } from '@/config/client';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorSummary } from '@/components/shared';
import { getCsrfToken } from '@/lib/api-client';

function ResendInvite() {
  const params = useParams();
  const router = useRouter();
  const orgId = params.orgId as string;
  const inviteId = params.inviteId as string;
  const manageUrl = `/publish/org/${orgId}/manage`;

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleConfirm = async () => {
    setIsSubmitting(true);
    setError('');

    try {
      const response = await fetch(`/api/publish/organisation/invites/${inviteId}/resend/`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'X-CSRFToken': getCsrfToken() },
      });

      if (!response.ok) {
        setError('Unable to resend this invite. Please try again.');
        setIsSubmitting(false);
        return;
      }

      router.push(manageUrl);
      router.refresh();
    } catch {
      setError('Unable to resend this invite. Please try again.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <Breadcrumbs
          items={[
            { label: 'Bus Open Data Service', href: HOSTS.www },
            { label: 'Publish Bus Open Data', href: HOSTS.publish },
            { label: 'User management', href: manageUrl },
            { label: 'Resend invite', current: true },
          ]}
        />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            {error && <ErrorSummary errors={[error]} summaryId="invite-resend-error-title" />}
            <h1 className="govuk-heading-l">Resend this invitation?</h1>
            <div className="govuk-button-group">
              <button type="button" className="govuk-button" disabled={isSubmitting} onClick={handleConfirm}>
                Confirm
              </button>
              <button type="button" className="govuk-button govuk-button--secondary" onClick={() => router.push(manageUrl)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ResendInvitePage() {
  return (
    <ProtectedRoute>
      <ResendInvite />
    </ProtectedRoute>
  );
}
