'use client';

/**
 * Agent removed from the organisation.
 *
 * Mirrors Django's users/remove_agent_user_from_org_success.html
 * (UserAgentRemoveSuccessView).
 */

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { OrgAdminRoute } from '@/components/auth/OrgAdminRoute';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/lib/api-client';

interface AgentInviteDetail {
  agentEmail: string;
}

function RemoveAgentSuccessContent() {
  const params = useParams();
  const { user } = useAuth();
  const inviteId = params.pk as string;
  const manageUrl = user?.organisation_id
    ? `/account/manage/${user.organisation_id}`
    : '/account';

  const [agentEmail, setAgentEmail] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isCancelled = false;

    api
      .get<AgentInviteDetail>(`/api/auth/agent/invite/${inviteId}/`)
      .then((data) => {
        if (!isCancelled) setAgentEmail(data.agentEmail);
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

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            {isLoading && <p className="govuk-body">Loading...</p>}
            {!isLoading && error && <p className="govuk-body">{error}</p>}
            {!isLoading && agentEmail && (
              <>
                <h1 className="govuk-heading-xl">Agent has been removed</h1>
                <p className="govuk-body">
                  Agent user <b>{agentEmail}</b> has been removed and will no longer be able to act
                  on behalf of your organisation.
                </p>
                <Link
                  href={manageUrl}
                  role="button"
                  draggable="false"
                  className="govuk-button govuk-!-margin-top-5"
                  data-module="govuk-button"
                >
                  Go back to user management
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function RemoveAgentSuccessPage() {
  return (
    <OrgAdminRoute>
      <RemoveAgentSuccessContent />
    </OrgAdminRoute>
  );
}
