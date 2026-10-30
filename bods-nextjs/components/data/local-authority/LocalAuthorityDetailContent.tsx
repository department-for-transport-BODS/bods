'use client';

/**
 * Local Transport Authority profile (data host, `/local-authority/detail/?auth_ids=...`)
 *
 * Source: transit_odp/browse/templates/browse/local_authority/local_authority_detail.html
 * View: transit_odp/browse/views/local_authority.py - LocalAuthorityDetailView
 * API: transit_odp/browse/views/api.py - local_authority_detail_api
 */

import Link from 'next/link';
import { notFound, useSearchParams } from 'next/navigation';
import { Suspense, useCallback, useEffect, useRef, type ReactNode } from 'react';
import {
  AvlRequireAttentionHelp,
  FaresRequireAttentionHelp,
  LicenceComplianceHelp,
  OverallRequireAttentionHelp,
  TimetableRequireAttentionHelp,
} from '@/components/data/operators/OperatorHelpModals';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorDisplay } from '@/components/shared/ErrorDisplay';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { dataPath, wwwPath } from '@/config/client';
import { useApiResource } from '@/hooks/useApiResource';
import { ApiError, api } from '@/lib/api-client';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';
import {
  LOCAL_AUTHORITY_DETAIL_API_PATH,
  licenceDetailUrl,
  localAuthorityDetailUrl,
  localAuthorityExportUrls,
  truncateChars,
  type LocalAuthorityDetail,
} from '@/lib/local-authority';

const NOT_FOUND = 'not-found';

function LicenceAccordion({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = ref.current;
    if (!root) return;
    import('govuk-frontend')
      .then(({ Accordion }) => {
        try {
          new Accordion(root);
        } catch {
          // Already initialised (React strict mode runs effects twice).
        }
      })
      .catch(() => undefined);
  }, []);

  return (
    <div ref={ref} className="govuk-accordion" data-module="govuk-accordion" id="accordion-default">
      <div className="govuk-accordion__section">
        <div className="govuk-accordion__section-header">
          <h2 className="govuk-accordion__section-heading">
            <span className="govuk-accordion__section-button" id="accordion-default-heading-1">
              Licence number
            </span>
          </h2>
        </div>
        <div id="accordion-default-content-1" className="govuk-accordion__section-content">
          {children}
        </div>
      </div>
    </div>
  );
}

function RequireAttentionStat({ value, help }: { value: number | null; help: ReactNode }) {
  return (
    <div id="feed-stat-list" className="govuk-grid-row">
      <div className="govuk-grid-column-one-half">
        <div className="feed-stat">
          <span className="feed-stat__value">{value}</span>
          <span className="feed-stat__label">
            Services requiring attention
            <b className="govuk-!-font-size-16 bods-relative-bottom">{help}</b>
          </span>
        </div>
      </div>
    </div>
  );
}

function SectionBreak() {
  return <hr className="govuk-section-break govuk-section-break--m govuk-section-break--visible" />;
}

function LocalAuthorityDetailInner() {
  const searchParams = useSearchParams();
  const authIds = searchParams.get('auth_ids') ?? '';

  const fetchDetail = useCallback(async (): Promise<LocalAuthorityDetail | typeof NOT_FOUND> => {
    try {
      return await api.get<LocalAuthorityDetail>(
        `${LOCAL_AUTHORITY_DETAIL_API_PATH}?auth_ids=${encodeURIComponent(authIds)}`,
      );
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) return NOT_FOUND;
      throw err;
    }
  }, [authIds]);

  const { data, isLoading, error } = useApiResource(fetchDetail, 'Failed to load local transport authority');

  if (data === NOT_FOUND) return notFound();

  const detail = data;

  if (isLoading || (!detail && !error)) {
    return (
      <div className="govuk-width-container">
        <LoadingSpinner message="Loading local transport authority" />
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="govuk-width-container">
        <ErrorDisplay message={error || 'Failed to load local transport authority'} />
      </div>
    );
  }

  const completePages = detail.isCompleteServicePagesActive;
  const exportUrls = localAuthorityExportUrls(detail.authIds);

  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={hostBreadcrumbs(
          'data',
          { label: 'Local Authority Profiles', href: dataPath('/local-authority') },
          { label: truncateChars(detail.name, 19), href: localAuthorityDetailUrl(detail.authIds) },
        )}
      />

      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-l">{detail.name}</h1>
            {!completePages && (
              <h2 className="govuk-heading-m govuk-!-margin-top-3">
                Timetables data{' '}
                {detail.servicesRequireAttentionPercentage === 0 ? (
                  <span className="govuk-tag govuk-tag--green">Compliant</span>
                ) : (
                  <span className="govuk-tag--red govuk-tag">Not Compliant</span>
                )}
              </h2>
            )}
            <p className="govuk-body">
              The service codes summarised here are registered with the OTC and are in scope of BODS, but are not yet
              published in a complete and accurate way.
            </p>
            <p className="govuk-body">
              Please download the detailed export for more information on the compliance data relating to each service.
            </p>
            <div id="feed-stat-list" className="govuk-grid-row">
              {completePages ? (
                <div className="govuk-grid-column-two-thirds">
                  <div className="feed-stat">
                    <span className="feed-stat__value csp-inline">{detail.totalServicesRequiringAttention}</span>
                    <span className="csp-total-inscope-inseason">/{detail.totalInScopeInSeasonServices}</span>
                    <span className="feed-stat__label">
                      Total services that require attention
                      <b className="govuk-!-font-size-16 bods-relative-bottom">
                        <OverallRequireAttentionHelp />
                      </b>
                    </span>
                  </div>
                </div>
              ) : (
                <>
                  <div className="govuk-grid-column-one-half">
                    <div className="feed-stat">
                      <span className="feed-stat__value">{detail.totalInScopeInSeasonServices}</span>
                      <span className="feed-stat__label">
                        Registered in scope/
                        <br />
                        in season services
                      </span>
                    </div>
                  </div>
                  <div className="govuk-grid-column-one-half">
                    <div className="feed-stat">
                      <span className="feed-stat__value">{detail.servicesRequireAttentionPercentage}%</span>
                      <span className="feed-stat__label">
                        Services that
                        <br />
                        require attention
                      </span>
                    </div>
                  </div>
                </>
              )}
            </div>

            {detail.isAvlRequireAttentionActive ? (
              <ul className="govuk-list govuk-!-margin-top-5">
                <li>
                  <a className="govuk-link" href={exportUrls.complianceReport}>
                    Download compliance report
                  </a>
                </li>
              </ul>
            ) : (
              <>
                <ul className="govuk-list govuk-!-margin-top-5">
                  <li>
                    <a className="govuk-link" href={exportUrls.detailedExport}>
                      Download detailed export
                    </a>
                  </li>
                </ul>
                <ul className="govuk-list govuk-!-margin-top-5">
                  <li>
                    <a className="govuk-link" href={exportUrls.lineLevelExport}>
                      Download detailed line level export
                    </a>
                  </li>
                </ul>
              </>
            )}

            {completePages && (
              <>
                <SectionBreak />
                <h3 className="govuk-heading-m govuk-!-margin-top-7">Review data accuracy</h3>
                <p className="govuk-body">
                  The complete services page here provide a combined view of real time Location data, timetables and
                  fares data. Please review the data for each service and supply feedback if any issues exist.
                </p>
                <div id="feed-stat-list" className="govuk-grid-row">
                  <div className="govuk-grid-column-full">
                    <LicenceAccordion>
                      <ul className="govuk-list govuk-!-margin-bottom-1 licence-list">
                        {detail.licences.map((licence, index) => (
                          <li className="govuk-!-margin-bottom-3" key={`${licence.licenceNumber}-${index}`}>
                            <LicenceComplianceHelp nonCompliant={licence.nonCompliant} />
                            <a
                              className="govuk-link"
                              href={licenceDetailUrl(licence.licenceNumber, licence.licenceOrganisationId)}
                            >
                              {licence.licenceNumber}: {licence.operatorName}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </LicenceAccordion>
                  </div>
                </div>

                <SectionBreak />
                <h3 className="govuk-heading-m govuk-!-margin-top-7">Timetables data</h3>
                <RequireAttentionStat
                  value={detail.totalTimetableRecordsRequiringAttention}
                  help={<TimetableRequireAttentionHelp />}
                />

                {detail.isAvlRequireAttentionActive && (
                  <>
                    <SectionBreak />
                    <h3 className="govuk-heading-m govuk-!-margin-top-7">Location data</h3>
                    <RequireAttentionStat
                      value={detail.totalLocationRecordsRequiringAttention}
                      help={<AvlRequireAttentionHelp />}
                    />
                  </>
                )}

                {detail.isFaresRequireAttentionActive && (
                  <>
                    <SectionBreak />
                    <h3 className="govuk-heading-m govuk-!-margin-top-7">Fares data</h3>
                    <RequireAttentionStat
                      value={detail.totalFaresRecordsRequiringAttention}
                      help={<FaresRequireAttentionHelp />}
                    />
                  </>
                )}
                <hr className="govuk-section-break govuk-section-break--l govuk-section-break--visible" />
              </>
            )}
          </div>

          <div className="govuk-grid-column-one-third">
            <h3 className="govuk-heading-m">Need further help?</h3>
            <ul className="govuk-list">
              <li className="govuk-!-margin-bottom-3">
                <Link className="govuk-link" href={wwwPath('/contact')}>
                  Contact the service desk
                </Link>
              </li>
              <li className="govuk-!-margin-bottom-3">
                <Link className="govuk-link" href={dataPath('/guide-me')}>
                  Guide me
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export function LocalAuthorityDetailContent() {
  return (
    <Suspense fallback={null}>
      <LocalAuthorityDetailInner />
    </Suspense>
  );
}
