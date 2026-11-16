'use client';

/**
 * Org admin: remove an accepted agent from the organisation.
 * Django: `/account/agent/remove/<pk>/`
 */

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { OrgAdminRoute } from '@/components/auth/OrgAdminRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorSummary } from '@/components/shared';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/lib/api-client';
import { useBodsArea } from '@/lib/bods-host-context';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';

interface AgentInviteDetail {
  id: number;
  agentEmail: string;
}

function RemoveAgent() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const area = useBodsArea();
  const inviteId = params.pk as string;
  const manageUrl = user?.organisation_id
    ? `/account/manage/${user.organisation_id}`
    : '/account';

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
      await api.post(`/api/auth/agent/invite/${inviteId}/remove/`);

      router.push(`/account/agent/remove/${inviteId}/success`);
      router.refresh();
    } catch {
      setError('Unable to remove this agent. Please try again.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <Breadcrumbs
          items={hostBreadcrumbs(
            area,
            { label: 'User management', href: manageUrl },
            { label: 'Remove agent', current: true },
          )}
        />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            {isLoading && <p className="govuk-body">Loading...</p>}
            {!isLoading && error && <ErrorSummary errors={[error]} summaryId="agent-remove-error-title" />}

            {!isLoading && invite && (
              <>
                <h1 className="govuk-heading-l">
                  Are you sure you want to remove {invite.agentEmail} as an agent?
                </h1>
                <p className="govuk-body">They will no longer be able to publish or review data for your organisation.</p>
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

export default function RemoveAgentPage() {
  return (
    <OrgAdminRoute>
      <RemoveAgent />
    </OrgAdminRoute>
  );
}
