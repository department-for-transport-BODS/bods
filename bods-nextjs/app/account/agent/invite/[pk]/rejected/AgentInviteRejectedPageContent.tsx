'use client';

/**
 * Agent invite rejected.
 *
 * Mirrors Django's users/user_agent_invite_response_rejected.html
 * (UserAgentRejectResponseView).
 */

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { api } from '@/lib/api-client';
import { useBodsArea } from '@/lib/bods-host-context';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';

interface AgentInviteDetail {
  organisationName: string;
}

function AgentInviteRejectedContent() {
  const params = useParams();
  const area = useBodsArea();
  const inviteId = params.pk as string;

  const [organisationName, setOrganisationName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isCancelled = false;

    api
      .get<AgentInviteDetail>(`/api/auth/agent/invite/${inviteId}/`)
      .then((data) => {
        if (!isCancelled) setOrganisationName(data.organisationName);
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
        <Breadcrumbs items={hostBreadcrumbs(area, { label: 'My account', href: '/account' })} />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            {isLoading && <p className="govuk-body">Loading...</p>}
            {!isLoading && error && <p className="govuk-body">{error}</p>}
            {!isLoading && organisationName && (
              <>
                <h1 className="govuk-heading-xl">
                  You rejected the offer to act as an agent on behalf of {organisationName}
                </h1>
                <Link
                  href="/account"
                  role="button"
                  draggable="false"
                  className="govuk-button"
                  data-module="govuk-button"
                >
                  Return to My account
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AgentInviteRejectedPage() {
  return (
    <ProtectedRoute>
      <AgentInviteRejectedContent />
    </ProtectedRoute>
  );
}
