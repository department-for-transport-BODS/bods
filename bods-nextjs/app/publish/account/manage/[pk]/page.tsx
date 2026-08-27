'use client';

/**
 * User management (org admin)
 *
 * Mirrors Django's users/users_manage.html. `pk` is the organisation id
 * (`/account/manage/<org_id>/`).
 */

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { HOSTS, publishAppPath } from '@/config/client';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { api } from '@/lib/api-client';

interface Member {
  id: number;
  username: string;
  email: string;
  accountType: number;
  prettyAccountName: string;
  isActive: boolean;
  prettyStatus: string;
}

interface PendingInvite {
  id: number;
  email: string;
  accountType: number;
  sent: string | null;
}

interface AgentInvitation {
  id: number;
  organisationName: string;
  status: string;
  isPending: boolean;
  isAccepted: boolean;
}

interface MembersResponse {
  members: Member[];
  pendingInvites: PendingInvite[];
  pendingAgentInvites: AgentInvitation[];
}

function statusIndicatorClass(isActive: boolean): string {
  return isActive ? 'status-indicator--success' : 'status-indicator--inactive';
}

function ManageUsers() {
  const params = useParams();
  const orgId = params.pk as string;
  const inviteUrl = '/publish/account/manage/invite';

  const [data, setData] = useState<MembersResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isCancelled = false;

    api
      .get<MembersResponse>(`/api/publish/organisation/${orgId}/members/`)
      .then((response) => {
        if (!isCancelled) setData(response);
      })
      .catch(() => {
        if (!isCancelled) setError('Unable to load organisation members.');
      })
      .finally(() => {
        if (!isCancelled) setIsLoading(false);
      });

    return () => {
      isCancelled = true;
    };
  }, [orgId]);

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <Breadcrumbs
          items={[
            { label: 'Bus Open Data Service', href: HOSTS.www },
            { label: 'Publish Bus Open Data', href: HOSTS.publish },
            { label: 'My account', href: publishAppPath('/account') },
            { label: 'User management', current: true },
          ]}
        />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-full">
            <h1 className="govuk-heading-xl">User management</h1>

            {isLoading && <p className="govuk-body">Loading...</p>}
            {!isLoading && error && <p className="govuk-body">{error}</p>}

            {!isLoading && data && (
              <>
                <h2 className="govuk-heading-m">Manage your team's access</h2>
                <table className="govuk-table manage-users-table">
                  <thead className="govuk-table__head govuk-body-m">
                    <tr className="govuk-table__row">
                      <th className="govuk-table__header" scope="col">User</th>
                      <th className="govuk-table__header" scope="col">Type</th>
                      <th className="govuk-table__header" scope="col">Status</th>
                      <th className="govuk-table__header" scope="col">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="govuk-table__body govuk-body-m">
                    {data.members.map((member) => (
                      <tr key={member.id} className="govuk-table__row">
                        <td className="govuk-table__cell">
                          <Link className="govuk-link" href={`/publish/account/manage/${member.id}/detail`}>
                            {member.email}
                          </Link>
                        </td>
                        <td className="govuk-table__cell">{member.prettyAccountName}</td>
                        <td className="govuk-table__cell">{member.prettyStatus}</td>
                        <td className="govuk-table__cell"></td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {data.pendingInvites.length > 0 && (
                  <>
                    <h2 className="govuk-heading-m">Pending invites</h2>
                    <table className="govuk-table manage-users-table">
                      <thead className="govuk-table__head govuk-body-m">
                        <tr className="govuk-table__row">
                          <th className="govuk-table__header" scope="col">Email</th>
                          <th className="govuk-table__header" scope="col">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="govuk-table__body govuk-body-m">
                        {data.pendingInvites.map((invite) => (
                          <tr key={invite.id} className="govuk-table__row">
                            <td className="govuk-table__cell">{invite.email}</td>
                            <td className="govuk-table__cell">
                              <Link className="govuk-link" href={`/publish/account/manage/${invite.id}/re-invite`}>
                                Resend invite
                              </Link>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </>
                )}

                {data.pendingAgentInvites.length > 0 && (
                  <>
                    <h2 className="govuk-heading-m">Pending agent invites</h2>
                    <table className="govuk-table manage-users-table">
                      <thead className="govuk-table__head govuk-body-m">
                        <tr className="govuk-table__row">
                          <th className="govuk-table__header" scope="col">Organisation</th>
                          <th className="govuk-table__header" scope="col">Status</th>
                          <th className="govuk-table__header" scope="col">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="govuk-table__body govuk-body-m">
                        {data.pendingAgentInvites.map((invite) => (
                          <tr key={invite.id} className="govuk-table__row">
                            <td className="govuk-table__cell">{invite.organisationName}</td>
                            <td className="govuk-table__cell">
                              <span className="status-indicator status-indicator--unavailable">{invite.status}</span>
                            </td>
                            <td className="govuk-table__cell">
                              <Link className="govuk-link" href={`/publish/account/agent/invite/${invite.id}/resend`}>
                                Resend invite
                              </Link>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </>
                )}
              </>
            )}
            <Link className="govuk-button" href={inviteUrl}>Add new user</Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ManageUsersPage() {
  return (
    <ProtectedRoute>
      <ManageUsers />
    </ProtectedRoute>
  );
}
