'use client';

/**
 * Manage subscriptions (Find / data host)
 *
 * Mirrors Django's users/feeds_manage.html: subscribed datasets, unsubscribe
 * links, and mute-all-notifications. URL is `/account/manage` on the data host
 * (`users:feeds-manage`). Publish uses `/account/manage/<org_id>/` for user
 * management, so this page stays under `app/data/`.
 */

import { useEffect, useState, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { HOSTS, wwwPath } from '@/config/client';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { Pagination } from '@/components/shared/Pagination';
import { api } from '@/lib/api-client';

type SubscriptionDatasetType = 'TIMETABLE' | 'AVL' | 'FARES';

interface Subscription {
  id: number;
  name: string;
  datasetType: SubscriptionDatasetType;
  statusLabel: string;
  statusClass: string;
}

interface SubscriptionsResponse {
  muteNotifications: boolean;
  count: number;
  page: number;
  pageSize: number;
  totalPages: number;
  results: Subscription[];
}

function datasetSubscriptionPaths(
  datasetType: SubscriptionDatasetType,
  id: number,
): { detailUrl: string; unsubscribeUrl: string } {
  switch (datasetType) {
    case 'TIMETABLE':
      return { detailUrl: `/${id}`, unsubscribeUrl: `/${id}/subscription` };
    case 'AVL':
      return {
        detailUrl: `/avl/dataset/${id}`,
        unsubscribeUrl: `/avl/dataset/${id}/subscription`,
      };
    case 'FARES':
      return {
        detailUrl: `/fares/dataset/${id}`,
        unsubscribeUrl: `/fares/dataset/${id}/subscription`,
      };
    default: {
      const exhaustive: never = datasetType;
      return exhaustive;
    }
  }
}

function ManageSubscriptions() {
  const searchParams = useSearchParams();
  const page = Number(searchParams.get('page') || '1');
  const [data, setData] = useState<SubscriptionsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isMuting, setIsMuting] = useState(false);

  useEffect(() => {
    let isCancelled = false;

    setIsLoading(true);
    api
      .get<SubscriptionsResponse>(`/api/auth/subscriptions/?page=${page}`)
      .then((response) => {
        if (!isCancelled) {
          setData(response);
          setError('');
        }
      })
      .catch(() => {
        if (!isCancelled) setError('Unable to load your subscriptions.');
      })
      .finally(() => {
        if (!isCancelled) setIsLoading(false);
      });

    return () => {
      isCancelled = true;
    };
  }, [page]);

  const handleMuteChange = async (checked: boolean) => {
    if (!data) return;

    const previous = data.muteNotifications;
    setData({ ...data, muteNotifications: checked });
    setIsMuting(true);

    try {
      const response = await api.post<{ muteNotifications: boolean }>(
        '/api/auth/subscriptions/mute/',
        { muteNotifications: checked },
      );
      setData((current) =>
        current ? { ...current, muteNotifications: response.muteNotifications } : current,
      );
    } catch {
      setData((current) => (current ? { ...current, muteNotifications: previous } : current));
      setError('Unable to update notification settings.');
    } finally {
      setIsMuting(false);
    }
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <Breadcrumbs
          items={[
            { label: 'Bus Open Data Service', href: HOSTS.www },
            { label: 'My account', href: '/account' },
            { label: 'Manage subscriptions', current: true },
          ]}
        />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Manage subscriptions</h1>

            {isLoading && <p className="govuk-body">Loading...</p>}
            {!isLoading && error && <p className="govuk-body">{error}</p>}

            {!isLoading && !error && data && data.count === 0 && (
              <div className="govuk-inset-text">Your subscribed data sets will be listed here</div>
            )}

            {!isLoading && !error && data && data.count > 0 && (
              <>
                <table className="govuk-table">
                  <caption className="govuk-table__caption govuk-heading-m">Data sets</caption>
                  <thead className="govuk-table__head">
                    <tr className="govuk-table__row">
                      <th className="govuk-table__header" scope="col">Status</th>
                      <th className="govuk-table__header" scope="col">Data set</th>
                      <th className="govuk-table__header" scope="col">Data set ID</th>
                      <th className="govuk-table__header" scope="col">Action</th>
                    </tr>
                  </thead>
                  <tbody className="govuk-table__body">
                    {data.results.map((subscription) => {
                      const paths = datasetSubscriptionPaths(
                        subscription.datasetType,
                        subscription.id,
                      );

                      return (
                        <tr className="govuk-table__row" key={subscription.id}>
                          <td className="govuk-table__cell">
                            <span className={`status-indicator ${subscription.statusClass}`}>
                              {subscription.statusLabel}
                            </span>
                          </td>
                          <td className="govuk-table__cell">
                            <Link className="govuk-link" href={paths.detailUrl}>
                              {subscription.name}
                            </Link>
                          </td>
                          <td className="govuk-table__cell">
                            <Link className="govuk-link" href={paths.detailUrl}>
                              {subscription.id}
                            </Link>
                          </td>
                          <td className="govuk-table__cell">
                            <Link className="govuk-link" href={paths.unsubscribeUrl}>
                              Unsubscribe
                            </Link>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>

                <Pagination
                  currentPage={data.page}
                  totalPages={data.totalPages}
                  pageParam="page"
                  baseUrl="/account/manage"
                />

                <hr className="govuk-section-break govuk-section-break--l govuk-section-break" />

                <div className="govuk-form-group">
                  <fieldset className="govuk-fieldset">
                    <div className="govuk-checkboxes">
                      <div className="govuk-checkboxes__item">
                        <input
                          className="govuk-checkboxes__input"
                          id="mute"
                          name="mute_notifications"
                          type="checkbox"
                          checked={data.muteNotifications}
                          disabled={isMuting}
                          onChange={(event) => {
                            void handleMuteChange(event.target.checked);
                          }}
                        />
                        <label className="govuk-label govuk-checkboxes__label" htmlFor="mute">
                          Mute all subscriptions
                        </label>
                      </div>
                    </div>
                  </fieldset>
                </div>
              </>
            )}
          </div>

          <div className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-m">Need help with operator data requirements?</h2>
            <ul className="govuk-list app-list--nav govuk-!-font-size-19">
              <li>
                <Link className="govuk-link govuk-body" href="/guidance/requirements">
                  View our guidelines here
                </Link>
              </li>
              <li>
                <Link className="govuk-link govuk-body" href={wwwPath('/contact')}>
                  Contact the Bus Open Data Service
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ManageSubscriptionsPage() {
  return (
    <ProtectedRoute>
      <Suspense fallback={<p className="govuk-body">Loading...</p>}>
        <ManageSubscriptions />
      </Suspense>
    </ProtectedRoute>
  );
}
