'use client';

import { useCallback, useEffect, useRef, type ChangeEvent } from 'react';
import Link from 'next/link';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { HOSTS, publishAppPath } from '@/config/client';
import { useApiResource } from '@/hooks/useApiResource';
import { api } from '@/lib/api-client';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorDisplay, LoadingSpinner, Pagination } from '@/components/shared';
import { ReviewBanner } from './ReviewBanner';
import { ReviewListTable } from './ReviewListTable';
import {
  DATA_TYPE_OPTIONS,
  REVIEW_LIST_KINDS,
  TABS,
  djangoTitle,
  reviewListUrl,
} from './reviewListConfig';
import type { ReviewListKind, ReviewListResponse } from './types';
import './review-list.css';

interface ReviewListPageProps {
  kind: ReviewListKind;
}

function listApiPath(
  kind: ReviewListKind,
  orgId: string,
  searchParams: URLSearchParams,
): string {
  const query = new URLSearchParams();
  for (const key of ['tab', 'sort', 'page']) {
    const value = searchParams.get(key);
    if (value) {
      query.set(key, value);
    }
  }
  const suffix = query.toString();
  const base = `/api/publish/${REVIEW_LIST_KINDS[kind].apiNamespace}/list/${orgId}/`;
  return suffix ? `${base}?${suffix}` : base;
}

/**
 * The Django "Review my data" page for one data type
 * (publish/publish_list_base.html and its per-type feed_list.html).
 */
export function ReviewListPage({ kind }: ReviewListPageProps) {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;
  const config = REVIEW_LIST_KINDS[kind];
  const searchKey = searchParams.toString();
  const tabsRef = useRef<HTMLUListElement>(null);

  const fetchList = useCallback(
    () => api.get<ReviewListResponse>(listApiPath(kind, orgId, new URLSearchParams(searchKey))),
    [kind, orgId, searchKey],
  );
  const { data, isLoading, error } = useApiResource(fetchList, 'Unable to load your data sets');

  // Django snaps focus to the selected tab once the list has loaded.
  useEffect(() => {
    if (data) {
      const selected = tabsRef.current?.querySelector<HTMLElement>(
        '.govuk-tabs__list-item--selected > a',
      );
      selected?.focus();
    }
  }, [data]);

  const handleDataTypeChange = (event: ChangeEvent<HTMLSelectElement>) => {
    router.push(event.target.value);
  };

  if (error && !data) {
    return (
      <div className="govuk-width-container">
        <ErrorDisplay message={error} />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="govuk-width-container">
        <LoadingSpinner message={isLoading ? 'Loading' : undefined} />
      </div>
    );
  }

  const hasRows = data.results.length > 0;

  return (
    <>
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper govuk-!-padding-top-0 govuk-!-padding-bottom-0">
          <Breadcrumbs
            items={[
              { label: 'Bus Open Data Service', href: HOSTS.www },
              { label: 'Publish Bus Open Data', href: HOSTS.publish },
              ...(data.isAgentUser
                ? [{ label: 'Agent Dashboard', href: publishAppPath('/agent-dashboard') }]
                : []),
              {
                // Django links this crumb to the timetable feed-list on all three pages.
                label: djangoTitle(data.pageTitle),
                href: publishAppPath(`/org/${orgId}/dataset/timetable`),
              },
            ]}
          />
        </div>
      </div>

      <div className="app-masthead">
        <div className="govuk-width-container">
          <div className="govuk-!-margin-top-5">
            <h1 className="govuk-heading-xl app-masthead__title_agent_dashboard">{data.pageTitle}</h1>
            <p className="govuk-body">Publish, preview and manage your open data sets</p>
            <div className="govuk-grid-row govuk-!-margin-top-6">
              <div className="govuk-grid-column-full">
                <div className="review-banner review-list-banner">
                  <ReviewBanner kind={kind} orgId={orgId} banner={data.banner} />
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
                  value={reviewListUrl(orgId, kind)}
                  onChange={handleDataTypeChange}
                >
                  {DATA_TYPE_OPTIONS.map((option) => (
                    <option
                      key={option.kind}
                      value={reviewListUrl(orgId, option.kind)}
                      data-qa={option.qa}
                    >
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <hr className="govuk-section-break govuk-section-break--l" />

          <div className="govuk-tabs app-!-mb-1">
            <h2 className="govuk-tabs__title">Contents</h2>
            <ul className="govuk-tabs__list" ref={tabsRef}>
              {TABS.map(({ section, title }) => (
                <li
                  key={section}
                  className={`govuk-tabs__list-item ${data.tab === section ? 'govuk-tabs__list-item--selected' : ''}`}
                >
                  <Link className="govuk-tabs__tab" href={`?tab=${section}`}>
                    {title}
                  </Link>
                </li>
              ))}
            </ul>

            <section className="govuk-tabs__panel" id="active-feeds">
              <div className="govuk-grid-row">
                {hasRows ? (
                  <div>
                    <ReviewListTable
                      kind={kind}
                      orgId={orgId}
                      columns={data.columns}
                      rows={data.results}
                      searchParams={new URLSearchParams(searchKey)}
                    />
                    <Pagination
                      currentPage={data.page}
                      totalPages={data.totalPages}
                      showSinglePage
                    />
                  </div>
                ) : (
                  <p className="govuk-body-m">No data sets found</p>
                )}
              </div>
            </section>
          </div>

          <div className="govuk-grid-row">
            <div className="govuk-grid-column-two-thirds">
              <a
                role="button"
                className="govuk-button govuk-!-margin-top-5"
                href={publishAppPath(config.newPath(orgId))}
              >
                {config.publishNewLabel}
              </a>
            </div>
          </div>

          <div className="govuk-grid-row">
            <div className="govuk-grid-column-one-third">
              <h3 className="govuk-heading-s">
                <a className="govuk-link" href={publishAppPath('/guidance/operator-requirements')}>
                  Bus operator requirements
                </a>
              </h3>
              <p className="govuk-body">Guidance and support for English bus operators.</p>
            </div>
            <div className="govuk-grid-column-one-third">
              <h3 className="govuk-heading-s">
                <a
                  className="govuk-link"
                  href={publishAppPath('/guidance/local-authority-requirements')}
                >
                  Local authority requirements
                </a>
              </h3>
              <p className="govuk-body">Guidance and support for English local authorities.</p>
            </div>
            <div className="govuk-grid-column-one-third">
              <h3 className="govuk-heading-s">
                <a
                  className="govuk-link"
                  href={publishAppPath(`/account/manage/org-profile/${data.organisation.id}`)}
                >
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
