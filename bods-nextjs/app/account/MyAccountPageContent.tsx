'use client';

/**
 * My Account
 *
 * Mirrors Django's users/user_account.html: content depends on account type
 * (developer / single-org staff-or-admin / agent).
 */

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { dataPath } from '@/config/client';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { api } from '@/lib/api-client';
import { useBodsArea } from '@/lib/bods-host-context';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';

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
  const area = useBodsArea();
  const [account, setAccount] = useState<AccountData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isCancelled = false;

    api
      .get<AccountData>('/api/auth/account/')
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
    <>
      <div className="govuk-width-container">
        <Breadcrumbs items={hostBreadcrumbs(area, { label: 'My account', href: '/account' })} />
      </div>

      <div className="govuk-width-container">
        <div className="govuk-main-wrapper app-main-class">
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-two-thirds govuk-body">
            <h1 className="govuk-heading-xl govuk-!-margin-bottom-4">My account</h1>

            {isLoading && <p className="govuk-body">Loading...</p>}
            {!isLoading && error && <p className="govuk-body">{error}</p>}

            {!isLoading && !error && account?.isDeveloper && (
              <>
                <Link className="govuk-link app-nav-bold" href={dataPath('/account/manage')}>
                  Manage subscriptions
                </Link>
                <p className="govuk-body">Manage subscribed data sets and notification preferences.</p>
                <Link className="govuk-link app-nav-bold" href="/account/settings">
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
                    <th className="govuk-table__header">Account Type</th>
                    <th className="govuk-table__header">Actions</th>
                    <th className="govuk-table__header">Status</th>
                    <th className="govuk-table__header" aria-hidden="true" />
                  </tr>
                </thead>
                <tbody className="govuk-table__body govuk-body-m">
                  <tr className="govuk-table__row">
                    <td className="govuk-table__cell">{account.organisationName}</td>
                    <td className="govuk-table__cell">{account.prettyAccountName}</td>
                    <td className="govuk-table__cell" />
                    <td className="govuk-table__cell">
                      <span className={`status-indicator ${statusIndicatorClass(account.isActive)}`}>
                        {account.prettyStatus}
                      </span>
                    </td>
                    <td className="govuk-table__cell" />
                  </tr>
                </tbody>
              </table>
            )}

            {!isLoading && !error && account?.isAgentUser && (
              <>
                <p className="govuk-body">
                  Manage organisation for which you are acting as an Agent. You can accept or deny requests to
                  become an organisation&apos;s agent by clicking respond, and remove yourself from an organisation
                  by choosing leave organisation.
                </p>
                <table className="govuk-table manage-users-table">
                  <thead className="govuk-table__head govuk-body-m">
                    <tr className="govuk-table__row">
                      <th className="govuk-table__header" scope="col">Organisations</th>
                      <th className="govuk-table__header">Actions</th>
                      <th className="govuk-table__header">Status</th>
                      <th className="govuk-table__header" aria-hidden="true" />
                    </tr>
                  </thead>
                  <tbody className="govuk-table__body govuk-body-m">
                    {(account.agentInvitations || []).map((invite) => (
                      <tr key={invite.id} className="govuk-table__row">
                        <td className="govuk-table__cell">{invite.organisationName}</td>
                        <td className="govuk-table__cell">
                          {invite.isPending && (
                            <Link className="govuk-link" href={`/account/agent/invite/${invite.id}`}>
                              Respond
                            </Link>
                          )}
                          {invite.isAccepted && (
                            <Link className="govuk-link" href={`/account/agent/leave/${invite.id}`}>
                              Leave Organisation
                            </Link>
                          )}
                        </td>
                        <td className="govuk-table__cell">
                          <span
                            className={`status-indicator ${invite.isAccepted ? 'status-indicator--success' : 'status-indicator--unavailable'}`}
                          >
                            {invite.status.charAt(0).toUpperCase() + invite.status.slice(1)}
                          </span>
                        </td>
                        <td className="govuk-table__cell" />
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}

            {!isLoading && !error && !account?.isDeveloper && !account?.isSingleOrgUser && !account?.isAgentUser && (
              <>
                <Link className="govuk-link app-nav-bold" href="/account/settings">
                  Account settings
                </Link>
                <p className="govuk-body">Edit your account settings and notification preferences.</p>
              </>
            )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default function MyAccountPage() {
  return (
    <ProtectedRoute>
      <MyAccount />
    </ProtectedRoute>
  );
}
