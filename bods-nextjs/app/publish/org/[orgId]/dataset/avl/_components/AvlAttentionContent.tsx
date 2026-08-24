'use client';

import { useParams, useSearchParams } from 'next/navigation';
import { useCallback } from 'react';
import { useApiResource } from '@/hooks/useApiResource';
import { Pagination } from '@/components/shared/Pagination';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { HOSTS } from '@/config/client';

interface AttentionSummary {
  available: boolean;
  servicesRequiringAttention: number | null;
  totalInScopeInSeasonServices: number | null;
  percentage: number;
}

interface AttentionRow {
  licenceNumber: string;
  serviceCode: string;
  lineNumber: string;
}

interface AttentionPageResponse {
  summary: AttentionSummary;
  rows: AttentionRow[];
  pagination: {
    currentPage: number;
    totalPages: number;
  };
  query: string;
  exportUrl: string | null;
  noResults: boolean;
}

export function AvlAttentionContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;
  const query = (searchParams.get('q') || '').trim();
  const pageParam = searchParams.get('page') || '1';
  const parsedPage = Number.parseInt(pageParam, 10);
  const page = Number.isNaN(parsedPage) || parsedPage < 1 ? 1 : parsedPage;

  const loadAttentionData = useCallback(async (): Promise<AttentionPageResponse> => {
    const response = await fetch(
      `/api/publish/avl/requires-attention/${encodeURIComponent(orgId)}/?q=${encodeURIComponent(query)}&page=${page}`,
      {
        method: 'GET',
        credentials: 'include',
        cache: 'no-store',
      },
    );

    const payload = (await response.json().catch(() => ({}))) as AttentionPageResponse & { error?: string };

    if (!response.ok) {
      throw new Error(payload.error || `Unable to load service code attention data (status ${response.status})`);
    }

    return payload;
  }, [orgId, query, page]);

  const {
    data,
    isLoading,
    error,
  } = useApiResource<AttentionPageResponse>(loadAttentionData, 'Unable to load service code attention data.');

  const summary = data?.summary;
  const backUrl = `/publish/org/${orgId}/dataset/avl`;
  const pageBaseUrl = `/publish/org/${orgId}/dataset/avl/attention`;

  return (
    <>
      <div className="govuk-width-container">
        <Breadcrumbs
          items={[
            { label: 'Bus Open Data Service', href: HOSTS.www },
            { label: 'Publish Bus Open Data', href: HOSTS.publish },
            {
              label: 'Review My Bus Location Data',
              href: backUrl,
            },
            {
              label: 'Service Codes Requiring Attention',
              href: pageBaseUrl,
              current: true,
            },
          ]}
        />
      </div>

      <div className="app-masthead">
        <div className="govuk-width-container">
          <div className="govuk-grid-row govuk-!-margin-top-5">
            <div className="govuk-grid-column-two-thirds">
              <h1 className="govuk-heading-xl app-masthead__title">Service codes requiring attention</h1>
              <p className="govuk-body">
                The service codes listed here are registered with the OTC and are in scope of BODS, but are not yet
                published in a complete and accurate way.
              </p>
              <p className="govuk-body">
                Download the detailed export at the bottom of the page to determine the reason your service code is
                listed here.
              </p>
              <p className="govuk-body">Contact the service desk if you have any questions or require any support.</p>
            </div>
          </div>
        </div>
      </div>

      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          {isLoading && <p className="govuk-body">Loading service codes...</p>}
          {error && <p className="govuk-body govuk-error-message">{error}</p>}

          {!isLoading && !error && (
            <>
              <div className="govuk-grid-row govuk-!-margin-bottom-9">
                <div className="govuk-grid-column-one-quarter">
                  <div className="feed-stat">
                    <span className="feed-stat__value">{summary?.totalInScopeInSeasonServices ?? 0}</span>
                    <span className="feed-stat__label govuk-!-font-size-16" style={{ maxWidth: '11rem' }}>
                      Total in scope/in season registered services
                    </span>
                  </div>
                </div>
                <div className="govuk-grid-column-one-quarter">
                  <div className="feed-stat">
                    <span className="feed-stat__value">{summary?.percentage ?? 0}%</span>
                    <span
                      className="feed-stat__label govuk-!-font-size-16 govuk-!-margin-bottom-2"
                      style={{ maxWidth: '11rem' }}
                    >
                      Services requiring attention
                    </span>
                    {(summary?.percentage ?? 0) === 0 ? (
                      <span className="letter-spacing-0 govuk-tag--green govuk-tag">Compliant</span>
                    ) : (
                      <span className="letter-spacing-0 govuk-tag--red govuk-tag">Not Compliant</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="govuk-grid-row govuk-!-margin-top-0">
                <form className="govuk-grid-column-full" method="GET" action={pageBaseUrl}>
                  <div className="govuk-form-group">
                    <label className="govuk-label" htmlFor="q">
                      Search for a licence number, service code or line number
                    </label>
                    <div className="app-data-browser__searchbox" style={{ maxWidth: '500px' }}>
                      <input className="app-data-browser__searchbox-input" id="q" name="q" type="text" defaultValue={query} />
                      <button className="app-data-browser__searchbox-button" type="submit" aria-label="Search">
                        <svg width="21" height="22" viewBox="0 0 21 22" xmlns="http://www.w3.org/2000/svg">
                          <g transform="translate(-760 -316)" fill="none" fillRule="evenodd">
                            <path
                              d="M776.594 331.75a9.418 9.418 0 0 0 2.428-6.296c0-5.213-4.268-9.454-9.51-9.454-5.244 0-9.512 4.242-9.512 9.454 0 5.213 4.268 9.455 9.51 9.455a9.523 9.523 0 0 0 5.04-1.444l4.176 4.152c.25.248.59.383.931.383.34 0 .681-.136.931-.383a1.295 1.295 0 0 0 .023-1.873l-4.017-3.994zm-13.939-6.296c0-3.746 3.065-6.814 6.855-6.814 3.792 0 6.833 3.068 6.833 6.814s-3.064 6.815-6.832 6.815-6.856-3.047-6.856-6.815z"
                              fill="#FFF"
                              fillRule="nonzero"
                            />
                          </g>
                        </svg>
                      </button>
                    </div>
                  </div>
                </form>
              </div>

              {data?.noResults ? (
                <div className="govuk-grid-row">
                  <div className="govuk-grid-column-two-thirds">
                    <h2 className="govuk-heading-m">Sorry, no results found for your search</h2>
                    <p className="govuk-body govuk-!-margin-top-8">
                      <b>Having trouble finding what you want?</b>
                    </p>
                    <ul className="govuk-list govuk-list--bullet">
                      <li>Check your spelling and try again</li>
                      <li>Use another search term</li>
                    </ul>
                  </div>
                </div>
              ) : (
                <div className="govuk-grid-row">
                  <div className="govuk-grid-column-full custom_govuk_table_border">
                    <table className="custom_govuk_table govuk-table">
                      <thead className="govuk-table__head">
                        <tr className="govuk-table__row">
                          <th className="govuk-table__header" scope="col">
                            Licence number
                          </th>
                          <th className="govuk-table__header" scope="col">
                            Service code
                          </th>
                          <th className="govuk-table__header" scope="col">
                            Line
                          </th>
                        </tr>
                      </thead>
                      <tbody className="govuk-table__body">
                        {data?.rows.map((row) => (
                          <tr className="govuk-table__row" key={`${row.licenceNumber}-${row.serviceCode}-${row.lineNumber}`}>
                            <td className="govuk-table__cell">{row.licenceNumber}</td>
                            <td className="govuk-table__cell">{row.serviceCode}</td>
                            <td className="govuk-table__cell">{row.lineNumber}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="govuk-grid-column-full">
                    <Pagination
                      currentPage={data?.pagination.currentPage ?? 1}
                      totalPages={data?.pagination.totalPages ?? 1}
                      pageParam="page"
                      baseUrl={pageBaseUrl}
                    />
                  </div>
                </div>
              )}

              <div className="govuk-grid-row govuk-!-margin-top-5">
                <div className="govuk-grid-column-full">
                  <p className="govuk-body-s">Use the link below to download and view the entire list of service codes</p>
                  {data?.exportUrl ? (
                    <p className="govuk-body-s">
                      <a className="govuk-link" href={data.exportUrl}>
                        Download detailed export
                      </a>
                    </p>
                  ) : null}
                </div>
              </div>
            </>
          )}

          <div className="govuk-grid-row govuk-!-margin-top-5">
          </div>
        </div>
      </div>
    </>
  );
}
