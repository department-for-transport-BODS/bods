'use client';

/**
 * My Account
 *
 * Mirrors Django's users/user_account.html: content depends on account type
 * (developer / single-org staff-or-admin / agent).
 */

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { HOSTS, publishAppPath, dataPath } from '@/config/client';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { api } from '@/lib/api-client';

interface AgentInvitation {
  id: number;
  organisationName: string;
  status: string;
  isPending: boolean;
  isAccepted: boolean;
}

interface AccountData {
  isDeveloper: boolean;
  isSingleOrgUser: boolean;
  isAgentUser: boolean;
  isOrgAdmin: boolean;
  prettyAccountName: string;
  isActive: boolean;
  prettyStatus: string;
  organisationId: number | null;
  organisationName: string | null;
  agentInvitations: AgentInvitation[] | null;
}

function statusIndicatorClass(isActive: boolean): string {
  return isActive ? 'status-indicator--success' : 'status-indicator--inactive';
}

function MyAccount() {
  const [account, setAccount] = useState<AccountData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isCancelled = false;

    api
      .get<AccountData>('/api/publish/account/')
      .then((data) => {
        if (!isCancelled) setAccount(data);
      })
      .catch(() => {
        if (!isCancelled) setError('Unable to load your account details.');
      })
      .finally(() => {
        if (!isCancelled) setIsLoading(false);
      });

    return () => {
      isCancelled = true;
    };
  }, []);

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <Breadcrumbs
          items={[
            { label: 'Bus Open Data Service', href: HOSTS.www },
            { label: 'Publish Bus Open Data', href: HOSTS.publish },
            { label: 'My account', current: true },
          ]}
        />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl govuk-!-margin-bottom-4">My account</h1>

            {isLoading && <p className="govuk-body">Loading...</p>}
            {!isLoading && error && <p className="govuk-body">{error}</p>}

            {!isLoading && !error && account?.isDeveloper && (
              <>
                <Link className="govuk-link app-nav-bold" href={dataPath('/account/manage')}>
                  Manage subscriptions
                </Link>
                <p className="govuk-body">Manage subscribed data sets and notification preferences.</p>
                <Link className="govuk-link app-nav-bold" href={publishAppPath('/account/settings')}>
                  Account settings
                </Link>
                <p className="govuk-body">Edit your account settings and notification preferences.</p>
              </>
            )}

            {!isLoading && !error && account?.isSingleOrgUser && (
              <table className="govuk-table manage-users-table">
                <thead className="govuk-table__head govuk-body-m">
                  <tr className="govuk-table__row">
                    <th className="govuk-table__header" scope="col">Organisation</th>
                    <th className="govuk-table__header" scope="col">Account Type</th>
                    <th className="govuk-table__header" scope="col">Actions</th>
                    <th className="govuk-table__header" scope="col">Status</th>
                  </tr>
                </thead>
                <tbody className="govuk-table__body govuk-body-m">
                  <tr className="govuk-table__row">
                    <td className="govuk-table__cell">{account.organisationName}</td>
                    <td className="govuk-table__cell">{account.prettyAccountName}</td>
                    <td className="govuk-table__cell">
                      {/* Python version has nothing here? */}
                    </td>
                    <td className="govuk-table__cell">
                      <span className={`status-indicator ${statusIndicatorClass(account.isActive)}`}>
                        {account.prettyStatus}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            )}

            {!isLoading && !error && account?.isAgentUser && (
              <>
                <p className="govuk-body">
                  Manage organisations for which you are acting as an agent. You can accept or deny requests to
                  become an organisation&apos;s agent by clicking respond, and remove yourself from an organisation
                  by choosing leave organisation.
                </p>
                <table className="govuk-table manage-users-table">
                  <thead className="govuk-table__head govuk-body-m">
                    <tr className="govuk-table__row">
                      <th className="govuk-table__header" scope="col">Organisations</th>
                      <th className="govuk-table__header" scope="col">Actions</th>
                      <th className="govuk-table__header" scope="col">Status</th>
                    </tr>
                  </thead>
                  <tbody className="govuk-table__body govuk-body-m">
                    {(account.agentInvitations || []).map((invite) => (
                      <tr key={invite.id} className="govuk-table__row">
                        <td className="govuk-table__cell">{invite.organisationName}</td>
                        <td className="govuk-table__cell">
                          {invite.isPending && (
                            <Link className="govuk-link" href={publishAppPath(`/account/agent/invite/${invite.id}`)}>
                              Respond
                            </Link>
                          )}
                          {invite.isAccepted && (
                            <Link className="govuk-link" href={publishAppPath(`/account/agent/leave/${invite.id}`)}>
                              Leave organisation
                            </Link>
                          )}
                        </td>
                        <td className="govuk-table__cell">
                          <span className={`status-indicator ${statusIndicatorClass(invite.isAccepted)}`}>
                            {invite.status.charAt(0).toUpperCase() + invite.status.slice(1)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}

            {!isLoading && !error && !account?.isDeveloper && !account?.isSingleOrgUser && !account?.isAgentUser && (
              <>
                <Link className="govuk-link app-nav-bold" href={publishAppPath('/account/settings')}>
                  Account settings
                </Link>
                <p className="govuk-body">Edit your account settings and notification preferences.</p>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function MyAccountPage() {
  return (
    <ProtectedRoute>
      <MyAccount />
    </ProtectedRoute>
  );
}
