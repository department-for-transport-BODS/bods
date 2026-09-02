'use client';

/**
 * Leave an organisation you're acting as an agent for.
 * Django: `/account/agent/leave/<pk>/`
 */

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ErrorSummary } from '@/components/shared';
import { api } from '@/lib/api-client';

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
      await api.post(`/api/auth/agent/invite/${inviteId}/leave/`);

      router.push(`/account/agent/leave/${inviteId}/success`);
      router.refresh();
    } catch {
      setError('Unable to leave this organisation. Please try again.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="govuk-width-container">
      <Link className="govuk-back-link" href="/account">
        Back
      </Link>
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            {isLoading && <p className="govuk-body">Loading...</p>}
            {!isLoading && error && <ErrorSummary errors={[error]} summaryId="agent-leave-error-title" />}

            {!isLoading && invite && (
              <>
                <h1 className="govuk-heading-xl">
                  Are you sure you would like to stop being an agent on behalf of{' '}
                  {invite.organisationName}?
                </h1>
                <p className="govuk-body-m govuk-!-margin-bottom-6">Please confirm your choice</p>
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
