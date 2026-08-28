'use client';

/**
 * Leave an organisation you're acting as an agent for.
 * Django: `/account/agent/leave/<pk>/`
 */

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { HOSTS } from '@/config/client';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorSummary } from '@/components/shared';
import { api, getCsrfToken } from '@/lib/api-client';

interface AgentInviteDetail {
  id: number;
  organisationName: string;
}

function AgentInviteLeave() {
  const params = useParams();
  const router = useRouter();
  const inviteId = params.pk as string;

  const [invite, setInvite] = useState<AgentInviteDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let isCancelled = false;

    api
      .get<AgentInviteDetail>(`/api/auth/agent/invite/${inviteId}/`)
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
      const response = await fetch(`/api/auth/agent/invite/${inviteId}/leave/`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'X-CSRFToken': getCsrfToken() },
      });

      if (!response.ok) {
        setError('Unable to leave this organisation. Please try again.');
        setIsSubmitting(false);
        return;
      }

      router.push('/account');
      router.refresh();
    } catch {
      setError('Unable to leave this organisation. Please try again.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <Breadcrumbs
          items={[
            { label: 'Bus Open Data Service', href: HOSTS.www },
            { label: 'My account', href: '/account' },
            { label: 'Leave organisation', current: true },
          ]}
        />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            {isLoading && <p className="govuk-body">Loading...</p>}
            {!isLoading && error && <ErrorSummary errors={[error]} summaryId="agent-leave-error-title" />}

            {!isLoading && invite && (
              <>
                <h1 className="govuk-heading-l">
                  Are you sure you want to leave {invite.organisationName}?
                </h1>
                <p className="govuk-body">You will no longer be able to publish or review data for this organisation.</p>
                <div className="govuk-button-group">
                  <button type="button" className="govuk-button" disabled={isSubmitting} onClick={handleConfirm}>
                    Confirm
                  </button>
                  <button
                    type="button"
                    className="govuk-button govuk-button--secondary"
                    onClick={() => router.push('/account')}
                  >
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

export default function AgentInviteLeavePage() {
  return (
    <ProtectedRoute>
      <AgentInviteLeave />
    </ProtectedRoute>
  );
}
