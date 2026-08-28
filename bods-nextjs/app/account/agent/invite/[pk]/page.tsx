'use client';

/**
 * Respond to an agent invite (accept or reject).
 * Django: `/account/agent/invite/<pk>/`
 */

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorSummary } from '@/components/shared';
import { api } from '@/lib/api-client';
import { useBodsArea } from '@/lib/bods-host-context';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';

interface AgentInviteDetail {
  id: number;
  organisationName: string;
  agentEmail: string;
  status: string;
}

function AgentInviteRespond() {
  const params = useParams();
  const router = useRouter();
  const area = useBodsArea();
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

  const respond = async (status: 'accepted' | 'rejected') => {
    setIsSubmitting(true);
    setError('');

    try {
      await api.post(`/api/auth/agent/invite/${inviteId}/respond/`, { status });

      router.push('/account');
      router.refresh();
    } catch {
      setError('Unable to respond to this invite. Please try again.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <Breadcrumbs
          items={hostBreadcrumbs(
            area,
            { label: 'My account', href: '/account' },
            { label: 'Respond to invite', current: true },
          )}
        />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            {isLoading && <p className="govuk-body">Loading...</p>}
            {!isLoading && error && <ErrorSummary errors={[error]} summaryId="agent-respond-error-title" />}

            {!isLoading && invite && (
              <>
                <h1 className="govuk-heading-xl">
                  Respond to an invitation from {invite.organisationName}
                </h1>
                <p className="govuk-body">
                  {invite.organisationName} has invited you to act as an agent on their behalf.
                </p>
                <div className="govuk-button-group">
                  <button
                    type="button"
                    className="govuk-button"
                    disabled={isSubmitting}
                    onClick={() => respond('accepted')}
                  >
                    Accept
                  </button>
                  <button
                    type="button"
                    className="govuk-button govuk-button--secondary"
                    disabled={isSubmitting}
                    onClick={() => respond('rejected')}
                  >
                    Reject
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

export default function AgentInviteRespondPage() {
  return (
    <ProtectedRoute>
      <AgentInviteRespond />
    </ProtectedRoute>
  );
}
