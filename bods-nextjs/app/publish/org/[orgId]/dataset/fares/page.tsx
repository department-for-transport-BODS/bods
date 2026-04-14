// This file implements the main page for managing fares datasets in the BODS Next.js frontend.
// It displays tabs for active, draft, and inactive datasets, fetches the list of published datasets from a custom API route, 
// and provides links to create new datasets and access guidance resources. The page also includes error handling for data fetching.
'use client';

import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { ChangeEvent, useEffect, useMemo, useState } from 'react';

type FaresTab = 'active' | 'draft' | 'archive';

interface FaresDataset {
  id: number;
  name?: string;
  modified?: string;
  shortDescription?: string;
  status?: string;
}

interface FaresListResponse {
  tab: FaresTab;
  results: FaresDataset[];
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
  const router = useRouter();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;
  const djangoApiBaseUrl = process.env.NEXT_PUBLIC_DJANGO_API_URL || 'http://localhost:8000';
  const nextCreateUrl = `/publish/org/${orgId}/dataset/fares/create`;
  const reviewDetailsUrl = '/publish/review';
  const operatorRequirementsUrl = '/publish/guide-me';
  const localAuthorityRequirementsUrl = '/publish/guide-me';
  const setUpLicenceNumbersUrl = '/publish/account';

  const tab = getTabFromSearchParams(searchParams.get('tab'));

  const [datasets, setDatasets] = useState<FaresDataset[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let isCancelled = false;

    const loadDatasets = async () => {
      setIsLoading(true);
      setError('');

      try {
        const response = await fetch(`${djangoApiBaseUrl}/api/fares/list/${orgId}/?tab=${tab}`, {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${globalThis.window.localStorage.getItem('bods.auth.access') || ''}`,
          },
        });

        const data = (await response.json().catch(() => ({}))) as Partial<FaresListResponse> & { error?: string };

        if (!response.ok) {
          throw new Error(data.error || `Unable to load fares datasets (${response.status})`);
        }

        if (!isCancelled) {
          setDatasets(Array.isArray(data.results) ? data.results : []);
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

    loadDatasets();

    return () => {
      isCancelled = true;
    };
  }, [djangoApiBaseUrl, orgId, tab]);

  const tabLinks = useMemo(
    () => ({
      active: `/publish/org/${orgId}/dataset/fares?tab=active`,
      draft: `/publish/org/${orgId}/dataset/fares?tab=draft`,
      archive: `/publish/org/${orgId}/dataset/fares?tab=archive`,
    }),
    [orgId],
  );

  const handleDataTypeChange = (event: ChangeEvent<HTMLSelectElement>) => {
    router.push(event.target.value);
  };

  return (
    <>
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper govuk-!-padding-top-0 govuk-!-padding-bottom-0">
          <div className="govuk-breadcrumbs">
            <ol className="govuk-breadcrumbs__list">
              <li className="govuk-breadcrumbs__list-item">
                <Link className="govuk-breadcrumbs__link" href="/data">
                  Bus Open Data Service
                </Link>
              </li>
              <li className="govuk-breadcrumbs__list-item">
                <Link className="govuk-breadcrumbs__link" href="/publish">
                  Publish Open Data Service
                </Link>
              </li>
              <li className="govuk-breadcrumbs__list-item" aria-current="page">
                Review My Fares Data
              </li>
            </ol>
          </div>
        </div>
      </div>

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
                      <span className="review-stat__top">0</span>
                    </div>
                    <p className="review-stat__description">Total consumer interactions with your data</p>
                    <i className="fas fa-play govuk-!-margin-right-1" aria-hidden="true"></i>
                    <a className="review-stat__link" href={reviewDetailsUrl}>
                      More details
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-two-thirds">
              <h2 className="govuk-heading-m">Choose data type</h2>
              <div className="select-wrapper govuk-!-width-one-third govuk-!-margin-bottom-7">
                <select
                  className="govuk-!-width-full govuk-select"
                  id="data-type-select"
                  name="data-type"
                  aria-label="Select data type"
                  value={`/publish/org/${orgId}/dataset/fares`}
                  onChange={handleDataTypeChange}
                >
                  <option value={`/publish/org/${orgId}/dataset/timetable`}>Timetables data</option>
                  <option value={`/publish/org/${orgId}/dataset/avl`}>Bus location data</option>
                  <option value={`/publish/org/${orgId}/dataset/fares`}>Fares data</option>
                </select>
              </div>
            </div>
          </div>

          <hr className="govuk-section-break govuk-section-break--l govuk-section-break--visible" />

          <div className="govuk-tabs app-!-mb-1">
            <h2 className="govuk-tabs__title">Contents</h2>
            <ul className="govuk-tabs__list">
              <li className={`govuk-tabs__list-item ${tab === 'active' ? 'govuk-tabs__list-item--selected' : ''}`}>
                <Link className="govuk-tabs__tab" href={tabLinks.active}>
                  Active
                </Link>
              </li>
              <li className={`govuk-tabs__list-item ${tab === 'draft' ? 'govuk-tabs__list-item--selected' : ''}`}>
                <Link className="govuk-tabs__tab" href={tabLinks.draft}>
                  Draft
                </Link>
              </li>
              <li className={`govuk-tabs__list-item ${tab === 'archive' ? 'govuk-tabs__list-item--selected' : ''}`}>
                <Link className="govuk-tabs__tab" href={tabLinks.archive}>
                  Inactive
                </Link>
              </li>
            </ul>

            <section className="govuk-tabs__panel" id="active-feeds">
              <div className="govuk-grid-row">
                {isLoading && <p className="govuk-body">Loading data sets...</p>}

                {error && (
                  <p className="govuk-body-m">
                    No data sets found
                  </p>
                )}

                {!isLoading && !error && datasets.length === 0 && (
                  <p className="govuk-body-m">No data sets found</p>
                )}

                {!isLoading && !error && datasets.length > 0 && (
                  <table className="custom_govuk_table govuk-table">
                    <thead className="govuk-table__head">
                      <tr className="govuk-table__row">
                        <th className="govuk-table__header" scope="col">
                          Status
                        </th>
                        <th className="govuk-table__header" scope="col" style={{ width: '20%' }}>
                          Data set name
                        </th>
                        <th className="govuk-table__header" scope="col">
                          Data set ID
                        </th>
                        <th className="govuk-table__header" scope="col" style={{ width: '25%' }}>
                          Last updated
                        </th>
                        <th className="govuk-table__header" scope="col" style={{ width: '20%' }}>
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
                            <a className="govuk-link" href={`/publish/org/${orgId}/dataset/fares/${dataset.id}/review`}>
                              {dataset.name || '-'}
                            </a>
                          </td>
                          <td className="govuk-table__cell">{dataset.id}</td>
                          <td className="govuk-table__cell">{formatDate(dataset.modified)}</td>
                          <td className="govuk-table__cell">{dataset.shortDescription || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
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
    </>
  );
}

export default function FaresPublishPage() {
  return (
    <ProtectedRoute>
      <FaresPublish />
    </ProtectedRoute>
  );
}

