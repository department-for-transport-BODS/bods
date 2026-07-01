'use client';

import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { api } from '@/lib/api-client';
import { formatDate } from '@/lib/utils/date';
import { useParams, useSearchParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { statusIndicatorClass, statusLabel } from './_components/avlStatus';
import { AvlMatchingHelpModal } from '@/components/publish/AvlMatchingHelpModal';

type AvlTab = 'active' | 'draft' | 'archive';

interface AVLFeed {
  id: number;
  name: string;
  modified?: string;
  description?: string;
  status?: string;
  avl_feed_status?: string;
  short_description?: string;
  percent_matching?: number | null;
  avl_feed_last_checked?: string | null;
}

function getTabFromSearchParams(value: string | null): AvlTab {
  if (value === 'draft' || value === 'archive') {
    return value;
  }
  return 'active';
}

function AvlManagement() {
  const params = useParams();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;

  const nextListUrl = `/publish/org/${orgId}/dataset/avl`;
  const nextCreateUrl = `/publish/org/${orgId}/dataset/avl/new`;
  const dataActivityUrl = `/publish/org/${orgId}/avl/data-activity/`;

  const tab = getTabFromSearchParams(searchParams.get('tab'));

  const [feeds, setFeeds] = useState<AVLFeed[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [sortBy, setSortBy] = useState<string>('modified');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    let isCancelled = false;

    const loadFeeds = async () => {
      setIsLoading(true);
      setError('');

      try {
        const response = await api.get<{ count: number; results: AVLFeed[] }>(
          `/api/avl/list/${orgId}?tab=${tab}&sort_by=${sortBy}&order=${sortOrder}`,
        );
        if (!isCancelled) {
          setFeeds(response.results);
        }
      } catch {
        if (!isCancelled) {
          setError('Unable to load bus location data feeds here. You can continue in the Django list view.');
          setFeeds([]);
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    };

    loadFeeds();

    return () => {
      isCancelled = true;
    };
  }, [orgId, tab, sortBy, sortOrder]);

  const tabLinks = useMemo(
    () => ({
      active: `/publish/org/${orgId}/dataset/avl?tab=active`,
      draft: `/publish/org/${orgId}/dataset/avl?tab=draft`,
      archive: `/publish/org/${orgId}/dataset/avl?tab=archive`,
    }),
    [orgId],
  );

  const handleDataTypeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    globalThis.location.assign(event.target.value);
  };

  const handleHeaderClick = (column: string) => {
    if (sortBy === column) {
      // Toggle sort order if same column clicked
      setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc');
    } else {
      // Change to new column, default to descending
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  const getSortIndicator = (column: string) => {
    if (sortBy !== column) return null;
    return sortOrder === 'desc' ? ' ▼' : ' ▲';
  };

  const sortButtonStyle: React.CSSProperties = {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    color: '#0087DC',
    font: 'inherit',
    padding: 0,
    textAlign: 'left',
  };

  return (
    <>
      <div className="govuk-width-container">
        <nav className="govuk-breadcrumbs" aria-label="Breadcrumb">
          <ol className="govuk-breadcrumbs__list">
            <li className="govuk-breadcrumbs__list-item">
              <Link className="govuk-breadcrumbs__link" href="/">
                Bus Open Data Service
              </Link>
            </li>
            <li className="govuk-breadcrumbs__list-item">
              <Link className="govuk-breadcrumbs__link" href="/publish/">
                Publish Open Data Service
              </Link>
            </li>
            <li className="govuk-breadcrumbs__list-item">
              <Link className="govuk-breadcrumbs__link" href={`/publish/org/${orgId}/dataset/avl`}>
                Review My Bus Location Data
              </Link>
            </li>
          </ol>
        </nav>
      </div>

      <div className="app-masthead">
        <div className="govuk-width-container">
          <div className="govuk-!-margin-top-5">
            <h1 className="govuk-heading-xl app-masthead__title_agent_dashboard">Review my bus location data</h1>
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
                    <a className="review-stat__link" href={dataActivityUrl}>
                      More details
                    </a>
                  </div>
                  <div className="review-stat">
                    <div>
                      <span className="review-stat__top">
                        Pending
                        <b className="govuk-!-font-size-16 bods-relative-bottom">
                          <AvlMatchingHelpModal />
                        </b>
                      </span>
                    </div>
                    <p className="review-stat__description">Weekly overall AVL to Timetables matching score</p>
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
              {isLoading && <p className="govuk-body">Loading data feeds...</p>}

              {!isLoading && error && (
                <p className="govuk-body-m">No data feeds found</p>
              )}

              {!isLoading && !error && feeds.length === 0 && (
                <p className="govuk-body-m">No data feeds found</p>
              )}

              {!isLoading && !error && feeds.length > 0 && (
                <table className="custom_govuk_table govuk-table">
                  <thead className="govuk-table__head">
                    <tr className="govuk-table__row">
                      <th className="govuk-table__header" scope="col">
                        <button onClick={() => handleHeaderClick('status')} style={sortButtonStyle}>
                          Status{getSortIndicator('status')}
                        </button>
                      </th>
                      <th className="govuk-table__header" scope="col">
                        <button onClick={() => handleHeaderClick('percent_matching')} style={sortButtonStyle}>
                          AVL to Timetable matching{getSortIndicator('percent_matching')}
                        </button>
                      </th>
                      <th className="govuk-table__header" scope="col">
                        <button onClick={() => handleHeaderClick('name')} style={sortButtonStyle}>
                          Data feed name{getSortIndicator('name')}
                        </button>
                      </th>
                      <th className="govuk-table__header" scope="col">
                        <button onClick={() => handleHeaderClick('id')} style={sortButtonStyle}>
                          Data feed ID{getSortIndicator('id')}
                        </button>
                      </th>
                      <th className="govuk-table__header" scope="col">
                        <button onClick={() => handleHeaderClick('avl_feed_last_checked')} style={sortButtonStyle}>
                          Last automated update{getSortIndicator('avl_feed_last_checked')}
                        </button>
                      </th>
                      <th className="govuk-table__header" scope="col">
                        <button onClick={() => handleHeaderClick('short_description')} style={sortButtonStyle}>
                          Short description{getSortIndicator('short_description')}
                        </button>
                      </th>
                    </tr>
                  </thead>
                  <tbody className="govuk-table__body">
                    {feeds.map((feed) => (
                      <tr key={feed.id} className="govuk-table__row">
                        <td className="govuk-table__cell">
                          <span className={`status-indicator ${statusIndicatorClass(feed.status)}`}>
                            {statusLabel(feed.status)}
                          </span>
                        </td>
                        <td className="govuk-table__cell">
                          {feed.percent_matching != null ? `${feed.percent_matching}%` : 'Pending'}
                        </td>
                        <td className="govuk-table__cell">
                          <Link
                            className="govuk-link"
                            href={`/publish/org/${orgId}/dataset/avl/${feed.id}`}
                          >
                            {feed.name || '-'}
                          </Link>
                        </td>
                        <td className="govuk-table__cell">{feed.id}</td>
                        <td className="govuk-table__cell">
                          {formatDate(feed.avl_feed_last_checked ?? feed.modified)}
                        </td>
                        <td className="govuk-table__cell">{feed.short_description || '-'}</td>
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

        <div className="govuk-grid-row govuk-!-margin-top-9">
          <div className="govuk-grid-column-one-third">
            <h3 className="govuk-heading-s">
              <a className="govuk-link" href="/publish/guidance/support/bus-operators/">
                Bus operator requirements
              </a>
            </h3>
            <p className="govuk-body">Guidance and support for English bus operators.</p>
          </div>
          <div className="govuk-grid-column-one-third">
            <h3 className="govuk-heading-s">
              <a className="govuk-link" href="/publish/guidance/support/local-authorities/">
                Local authority requirements
              </a>
            </h3>
            <p className="govuk-body">Guidance and support for English local authorities.</p>
          </div>
          <div className="govuk-grid-column-one-third">
            <h3 className="govuk-heading-s">
              <a className="govuk-link" href={`/publish/org/${orgId}/profile/`}>
                Set up licence numbers
              </a>
            </h3>
            <p className="govuk-body">
              Visit accounts settings to ensure licence numbers are set up correctly.
            </p>
          </div>
        </div>
      </div>
    </div>
    </>
  );
}

export default function AVLPage() {
  return (
    <ProtectedRoute>
      <AvlManagement />
    </ProtectedRoute>
  );
}

