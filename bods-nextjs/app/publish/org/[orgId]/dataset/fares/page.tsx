// This file implements the main page for managing fares datasets in the BODS Next.js frontend.
// It displays tabs for active, draft, and inactive datasets, fetches the list of published datasets from a custom API route, 
// and provides links to create new datasets and access guidance resources. The page also includes error handling for data fetching.
'use client';

import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { getPaginated } from '@/lib/api-client';
import { useParams, useSearchParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { config } from '@/config';

type FaresTab = 'active' | 'draft' | 'archive';

interface FaresDataset {
  id: number;
  name: string;
  modified?: string;
  description?: string;
  status?: string;
}

function getTabFromSearchParams(value: string | null): FaresTab {
  if (value === 'draft' || value === 'archive') {
    return value;
  }

  return 'active';
}

function formatDate(value?: string): string {
  if (!value) {
    return '-';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '-';
  }

  return new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(date);
}

function statusLabel(status?: string): string {
  if (!status) {
    return 'Unknown';
  }

  if (status === 'published' || status === 'live') {
    return 'Published';
  }

  if (status === 'draft' || status === 'success') {
    return 'Draft';
  }

  if (status === 'inactive' || status === 'expired') {
    return 'Inactive';
  }

  return status.charAt(0).toUpperCase() + status.slice(1);
}

function FaresPublish() {
  const params = useParams();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;
  const djangoApiBaseUrl = config.djangoApiBaseUrl
  const djangoPublishBaseUrl = `${djangoApiBaseUrl}.replace('://localhost', '://publish.localhost')`;
  const nextListUrl = `/publish/org/${orgId}/dataset/fares`;
  const nextCreateUrl = `/publish/org/${orgId}/dataset/fares/create`;
  const djangoAttentionUrl = `${djangoPublishBaseUrl}/org/${orgId}/dataset/fares/attention/`;
  const operatorRequirementsUrl = `${djangoPublishBaseUrl}/guidance/operator-requirements/`;
  const localAuthorityRequirementsUrl = `${djangoPublishBaseUrl}/guidance/local-authority-requirements/`;
  const setUpLicenceNumbersUrl = `${djangoPublishBaseUrl}/account/manage/org-profile/${orgId}/`;

  const tab = getTabFromSearchParams(searchParams.get('tab'));

  const [datasets, setDatasets] = useState<FaresDataset[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let isCancelled = false;

    const loadActiveDatasets = async () => {
      if (tab !== 'active') {
        setDatasets([]);
        return;
      }

      setIsLoading(true);
      setError('');

      try {
        const response = await getPaginated<FaresDataset>('/api/v1/fares/dataset/?status=published&limit=100');
        if (!isCancelled) {
          setDatasets(response.results);
        }
      } catch {
        if (!isCancelled) {
          setError('Unable to load fares datasets here. You can continue in the Django list view.');
          setDatasets([]);
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    };

    loadActiveDatasets();

    return () => {
      isCancelled = true;
    };
  }, [tab]);

  const tabLinks = useMemo(
    () => ({
      active: `/publish/org/${orgId}/dataset/fares?tab=active`,
      draft: `/publish/org/${orgId}/dataset/fares?tab=draft`,
      archive: `/publish/org/${orgId}/dataset/fares?tab=archive`,
    }),
    [orgId],
  );

  const handleDataTypeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    globalThis.location.assign(event.target.value);
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="app-masthead">
          <div className="govuk-width-container">
            <div className="govuk-!-margin-top-5">
              <h1 className="govuk-heading-xl app-masthead__title_agent_dashboard">Review my fares data</h1>
              <p className="govuk-body">Publish, preview and manage your open data sets</p>
              <div className="govuk-grid-row govuk-!-margin-top-6">
                <div className="govuk-grid-column-full">
                  <div className="review-banner">
                    <div className="review-stat">
                      <div>
                        <span className="review-stat__top">-</span>
                        <span className="review-stat__bottom">/-</span>
                      </div>
                      <p className="review-stat__description">Total service codes that require attention</p>
                      <i className="fas fa-play govuk-!-margin-right-1" aria-hidden="true"></i>
                      <a className="review-stat__link" href={djangoAttentionUrl}>
                        More details
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h2 className="govuk-heading-m">Choose data type</h2>
            <div className="select-wrapper govuk-!-width-one-third govuk-!-margin-bottom-7">
              <select
                className="govuk-!-width-full govuk-select"
                id="data-type-select"
                name="data-type"
                data-qa="data-type-select"
                aria-label="Select data type"
                value={nextListUrl}
                onChange={handleDataTypeChange}
              >
                <option value={`/publish/org/${orgId}/dataset/timetable`} data-qa="timetable-option">
                  Timetables data
                </option>
                <option value={`/publish/org/${orgId}/dataset/avl`} data-qa="avl-option">
                  Bus location data
                </option>
                <option value={`/publish/org/${orgId}/dataset/fares`} data-qa="fares-option">
                  Fares data
                </option>
              </select>
            </div>
          </div>
        </div>

        <hr className="govuk-section-break govuk-section-break--l govuk-section-break" />

        <div className="govuk-tabs app-!-mb-1">
          <h2 className="govuk-tabs__title">Contents</h2>
          <ul className="govuk-tabs__list">
            <li className={`govuk-tabs__list-item ${tab === 'active' ? 'govuk-tabs__list-item--selected' : ''}`}>
              <a className="govuk-tabs__tab" href={tabLinks.active}>
                Active
              </a>
            </li>
            <li className={`govuk-tabs__list-item ${tab === 'draft' ? 'govuk-tabs__list-item--selected' : ''}`}>
              <a className="govuk-tabs__tab" href={tabLinks.draft}>
                Draft
              </a>
            </li>
            <li className={`govuk-tabs__list-item ${tab === 'archive' ? 'govuk-tabs__list-item--selected' : ''}`}>
              <a className="govuk-tabs__tab" href={tabLinks.archive}>
                Inactive
              </a>
            </li>
          </ul>

          <section className="govuk-tabs__panel" id="active-feeds">
            <div className="govuk-grid-row">
              {tab === 'active' && isLoading && <p className="govuk-body">Loading data sets...</p>}

              {tab === 'active' && error && (
                <p className="govuk-body-m">
                  No data sets found
                </p>
              )}

              {tab === 'active' && !isLoading && !error && datasets.length === 0 && (
                <p className="govuk-body-m">No data sets found</p>
              )}

              {tab === 'active' && !isLoading && !error && datasets.length > 0 && (
                <table className="custom_govuk_table govuk-table">
                  <thead className="govuk-table__head">
                    <tr className="govuk-table__row">
                      <th className="govuk-table__header" scope="col">
                        Status
                      </th>
                      <th className="govuk-table__header app-table-col--20" scope="col">
                        Data set name
                      </th>
                      <th className="govuk-table__header" scope="col">
                        Data set ID
                      </th>
                      <th className="govuk-table__header app-table-col--25" scope="col">
                        Last updated
                      </th>
                      <th className="govuk-table__header app-table-col--20" scope="col">
                        Short description
                      </th>
                    </tr>
                  </thead>
                  <tbody className="govuk-table__body">
                    {datasets.map((dataset) => (
                      <tr key={dataset.id} className="govuk-table__row">
                        <td className="govuk-table__cell">
                          <span className="status-indicator status-indicator--success">{statusLabel(dataset.status)}</span>
                        </td>
                        <td className="govuk-table__cell">
                          <a className="govuk-link" href={`${djangoPublishBaseUrl}/org/${orgId}/dataset/fares/${dataset.id}/`}>
                            {dataset.name || '-'}
                          </a>
                        </td>
                        <td className="govuk-table__cell">{dataset.id}</td>
                        <td className="govuk-table__cell">{formatDate(dataset.modified)}</td>
                        <td className="govuk-table__cell">{dataset.description || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {(tab === 'draft' || tab === 'archive') && (
                <p className="govuk-body-m">No data sets found</p>
              )}
            </div>
          </section>
        </div>

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <Link className="govuk-button govuk-!-margin-top-5" href={nextCreateUrl}>
              Publish new data feeds
            </Link>
          </div>
        </div>

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-one-third">
            <h3 className="govuk-heading-s">
              <a className="govuk-link" href={operatorRequirementsUrl}>
                Bus operator requirements
              </a>
            </h3>
            <p className="govuk-body">Guidance and support for English bus operators.</p>
          </div>
          <div className="govuk-grid-column-one-third">
            <h3 className="govuk-heading-s">
              <a className="govuk-link" href={localAuthorityRequirementsUrl}>
                Local authority requirements
              </a>
            </h3>
            <p className="govuk-body">Guidance and support for English local authorities.</p>
          </div>
          <div className="govuk-grid-column-one-third">
            <h3 className="govuk-heading-s">
              <a className="govuk-link" href={setUpLicenceNumbersUrl}>
                Set up licence numbers
              </a>
            </h3>
            <p className="govuk-body">Visit accounts settings to ensure licence numbers are set up correctly.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function FaresPublishPage() {
  return (
    <ProtectedRoute>
      <FaresPublish />
    </ProtectedRoute>
  );
}

