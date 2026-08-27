'use client';

/**
 * User detail — mirrors Django's users/users_manage_detail.html.
 * `pk` is the member user id (`/account/manage/<user_id>/detail/`).
 */

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { HOSTS, publishAppPath } from '@/config/client';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/lib/api-client';

interface MemberDetail {
  id: number;
  username: string;
  email: string;
  prettyAccountName: string;
  isActive: boolean;
  prettyStatus: string;
  agentInviteId?: number | null;
  isSingleOrgUser: boolean;
  agentUser?: boolean;
}

function MemberDetailContent() {
  const params = useParams();
  const { user } = useAuth();
  const userId = params.pk as string;
  const manageUrl = user?.organisation_id
    ? `/publish/account/manage/${user.organisation_id}`
    : '/publish/account';

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
            { label: 'My account', href: publishAppPath('/account') },
            { label: 'User management', href: manageUrl },
            { label: 'User detail', current: true },
          ]}
        />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            {isLoading && <p className="govuk-body">Loading...</p>}
            {!isLoading && error && <p className="govuk-body">{error}</p>}

            {!isLoading && member && (
              <>
                <h1 className="govuk-heading-xl">{member.email}</h1>
                <h2 className="govuk-heading-m"> User detail </h2>
                <dl className="govuk-summary-list">
                <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">Status</dt>
                    <dd className="govuk-summary-list__value">{member.prettyStatus}</dd>
                </div>
                <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">Username</dt>
                    <dd className="govuk-summary-list__value">{member.username}</dd>
                </div>
                <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">User type</dt>
                    <dd className="govuk-summary-list__value">{member.prettyAccountName}</dd>
                </div>

                </dl>

                <div className="govuk-button-group">
                {member.isSingleOrgUser ? (
                  member.isActive ? (
                    <div className="govuk-button-group">
                      <Link className="govuk-button govuk-button--secondary" href={`/publish/account/manage/${member.id}/edit`}>
                        Edit
                      </Link>
                      <Link className="govuk-button govuk-button--secondary" href={`/publish/account/manage/${member.id}/archive`}>
                        Deactivate
                      </Link>
                    </div>
                  ) : (
                    <Link className="govuk-button govuk-button--secondary" href={`/publish/account/manage/${member.id}/activate`}>
                      Activate
                    </Link>
                )) : member.agentUser ? (
                      member.agentInviteId ? (
                        <Link
                          className="govuk-button govuk-button--secondary"
                          href={`/publish/account/agent/remove/${member.agentInviteId}`}
                        >
                          Remove
                        </Link>
                      ): (
                        <p className="govuk-body">No invitation found</p>
                      )
                    ) : null }
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
