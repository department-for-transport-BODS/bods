'use client';

/**
 * Member detail — mirrors Django's users/users_manage_detail.html.
 */

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { HOSTS } from '@/config/client';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { api } from '@/lib/api-client';

interface MemberDetail {
  id: number;
  username: string;
  email: string;
  prettyAccountName: string;
  isActive: boolean;
  prettyStatus: string;
  agentInviteId?: number | null;
}

function MemberDetailContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const userId = params.userId as string;
  const manageUrl = `/publish/org/${orgId}/manage`;

  const [member, setMember] = useState<MemberDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isCancelled = false;

    api
      .get<MemberDetail>(`/api/publish/organisation/members/${userId}/`)
      .then((data) => {
        if (!isCancelled) setMember(data);
      })
      .catch(() => {
        if (!isCancelled) setError('Unable to load this member.');
      })
      .finally(() => {
        if (!isCancelled) setIsLoading(false);
      });

    return () => {
      isCancelled = true;
    };
  }, [userId]);

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <Breadcrumbs
          items={[
            { label: 'Bus Open Data Service', href: HOSTS.www },
            { label: 'Publish Bus Open Data', href: HOSTS.publish },
            { label: 'User management', href: manageUrl },
            { label: 'Member detail', current: true },
          ]}
        />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            {isLoading && <p className="govuk-body">Loading...</p>}
            {!isLoading && error && <p className="govuk-body">{error}</p>}

            {!isLoading && member && (
              <>
                <h1 className="govuk-heading-xl">{member.username}</h1>

                <dl className="govuk-summary-list">
                  <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">Email</dt>
                    <dd className="govuk-summary-list__value">{member.email}</dd>
                  </div>
                  <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">Account type</dt>
                    <dd className="govuk-summary-list__value">{member.prettyAccountName}</dd>
                  </div>
                  <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">Status</dt>
                    <dd className="govuk-summary-list__value">{member.prettyStatus}</dd>
                  </div>
                </dl>

                <div className="govuk-button-group">
                  {member.agentInviteId ? (
                    <Link
                      className="govuk-button govuk-button--secondary"
                      href={`/publish/org/${orgId}/manage/agent-invite/${member.agentInviteId}/remove`}
                    >
                      Remove agent
                    </Link>
                  ) : (
                    <Link className="govuk-button" href={`/publish/org/${orgId}/manage/${member.id}/edit`}>
                      Edit
                    </Link>
                  )}
                  <Link className="govuk-button govuk-button--secondary" href={`/publish/org/${orgId}/manage/${member.id}/archive`}>
                    {member.isActive ? 'Deactivate' : 'Reactivate'}
                  </Link>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function MemberDetailPage() {
  return (
    <ProtectedRoute>
      <MemberDetailContent />
    </ProtectedRoute>
  );
}
