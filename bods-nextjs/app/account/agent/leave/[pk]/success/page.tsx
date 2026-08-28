'use client';

/**
 * Left an organisation as an agent.
 *
 * Mirrors Django's users/user_agent_leave_organisation_success.html
 * (UserAgentLeaveOrgSuccessView).
 */

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { api } from '@/lib/api-client';

interface AgentInviteDetail {
  organisationName: string;
}

function AgentLeaveSuccessContent() {
  const params = useParams();
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
        <div className="govuk-grid-row">
          {isLoading && <p className="govuk-body">Loading...</p>}
          {!isLoading && error && <p className="govuk-body">{error}</p>}
          {!isLoading && organisationName && (
            <>
              <div className="govuk-panel govuk-panel--confirmation govuk-!-padding-9">
                <h1 className="govuk-panel__title">
                  You are no longer an agent for {organisationName}
                </h1>
              </div>
              <p className="govuk-body">We have sent {organisationName} a confirmation email.</p>
              <Link
                href="/account"
                role="button"
                draggable="false"
                className="govuk-button govuk-!-margin-top-5"
                data-module="govuk-button"
              >
                Return to My account
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function AgentLeaveSuccessPage() {
  return (
    <ProtectedRoute>
      <AgentLeaveSuccessContent />
    </ProtectedRoute>
  );
}
