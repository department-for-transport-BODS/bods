'use client';

/**
 * Agent invite resent.
 *
 * Mirrors Django's users/resend_agent_invite_success.html
 * (ResendAgentUserInviteSuccessView).
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

function ResendAgentInviteSuccessContent() {
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
                <h1 className="govuk-heading-xl">Agent invite has been resent</h1>
                <p className="govuk-body">
                  Agent user invite has been resent to <b>{agentEmail}</b>.
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

export default function ResendAgentInviteSuccessPage() {
  return (
    <OrgAdminRoute>
      <ResendAgentInviteSuccessContent />
    </OrgAdminRoute>
  );
}
