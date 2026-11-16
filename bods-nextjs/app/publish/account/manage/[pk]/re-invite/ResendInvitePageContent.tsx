'use client';

/**
 * Org admin: resend a pending standard (non-agent) invite.
 * `pk` is the invitation id (`/account/manage/<invite_id>/re-invite/`).
 */

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { HOSTS } from '@/config/client';
import { OrgAdminRoute } from '@/components/auth/OrgAdminRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorSummary } from '@/components/shared';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/lib/api-client';
import { rememberInviteEmail } from '@/lib/auth/invite-email';

function ResendInvite() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const inviteId = params.pk as string;
  const manageUrl = user?.organisation_id
    ? `/account/manage/${user.organisation_id}`
    : '/account';

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleConfirm = async () => {
    setIsSubmitting(true);
    setError('');

    try {
      const invitation = await api.post<{ email: string }>(
        `/api/publish/organisation/invites/${inviteId}/resend/`,
      );

      rememberInviteEmail(invitation.email);
      router.push(`/account/manage/${inviteId}/re-invite/success`);
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
    <OrgAdminRoute>
      <ResendInvite />
    </OrgAdminRoute>
  );
}
