'use client';

/**
 * Org admin: resend a pending agent invite/confirmation email.
 * Django: `/account/agent/invite/<pk>/resend/`
 */

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { HOSTS } from '@/config/client';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorSummary } from '@/components/shared';
import { useAuth } from '@/hooks/useAuth';
import { api, getCsrfToken } from '@/lib/api-client';

interface AgentInviteDetail {
  id: number;
  agentEmail: string;
}

function ResendAgentInvite() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const inviteId = params.pk as string;
  const manageUrl = user?.organisation_id
    ? `/publish/account/manage/${user.organisation_id}`
    : '/publish/account';

  const [invite, setInvite] = useState<AgentInviteDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let isCancelled = false;

    api
      .get<AgentInviteDetail>(`/api/publish/agent/invite/${inviteId}/`)
      .then((data) => {
        if (!isCancelled) setInvite(data);
      })
      .catch(() => {
        if (!isCancelled) setError('Unable to load this invite.');
      })
      .finally(() => {
        if (!isCancelled) setIsLoading(false);
      });

    return () => {
      isCancelled = true;
    };
  }, [inviteId]);

  const handleConfirm = async () => {
    setIsSubmitting(true);
    setError('');

    try {
      const response = await fetch(`/api/publish/agent/invite/${inviteId}/resend/`, {
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
            {isLoading && <p className="govuk-body">Loading...</p>}
            {!isLoading && error && <ErrorSummary errors={[error]} summaryId="agent-resend-error-title" />}

            {!isLoading && invite && (
              <>
                <h1 className="govuk-heading-l">
                  Resend invite to {invite.agentEmail}?
                </h1>
                <div className="govuk-button-group">
                  <button type="button" className="govuk-button" disabled={isSubmitting} onClick={handleConfirm}>
                    Confirm
                  </button>
                  <button type="button" className="govuk-button govuk-button--secondary" onClick={() => router.push(manageUrl)}>
                    Cancel
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ResendAgentInvitePage() {
  return (
    <ProtectedRoute>
      <ResendAgentInvite />
    </ProtectedRoute>
  );
}
