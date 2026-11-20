'use client';

/**
 * Operator Profile detail (data host, `/operators/<pk>/`)
 *
 * Source: transit_odp/browse/templates/browse/operators/operator_detail.html
 * View: transit_odp/browse/views/operators.py - OperatorDetailView
 * API: transit_odp/browse/views/operators_api.py - operator_detail_api
 *
 * Django picks one of two layouts with the `is_complete_service_pages_active`
 * waffle flag; the API returns the resolved flags so both are rendered here.
 */

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlay } from '@fortawesome/free-solid-svg-icons';
import { notFound } from 'next/navigation';
import { useEffect, useRef, useState, type ReactNode } from 'react';
import { dataPath } from '@/config/client';
import {
  AvlRequireAttentionHelp,
  FaresRequireAttentionHelp,
  LicenceComplianceHelp,
  OverallRequireAttentionHelp,
  TimetableRequireAttentionHelp,
} from '@/components/data/operators/OperatorHelpModals';
import { FeedUrlPanel } from '@/components/data/operators/FeedUrlPanel';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorDisplay } from '@/components/shared/ErrorDisplay';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { ApiError, api } from '@/lib/api-client';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';
import {
  djangoValue,
  formatOperatorDate,
  operatorBrowseUrl,
  operatorContactUrl,
  operatorDetailApiPath,
  operatorDetailUrl,
  operatorGuidanceDataQualityUrl,
  operatorLicenceUrl,
  operatorPublishUrl,
  operatorsListUrl,
  truncateChars,
  type OperatorDetail,
} from '@/lib/operators';

interface OperatorDetailContentProps {
  operatorId: string;
}

function ComplianceTag({ compliant, className }: { compliant: boolean; className?: string }) {
  return compliant ? (
    <span className={`govuk-tag--green govuk-tag${className ? ` ${className}` : ''}`}>Compliant</span>
  ) : (
    <span className={`govuk-tag--red govuk-tag${className ? ` ${className}` : ''}`}>Not Compliant</span>
  );
}

function FeedStat({ value, label, help }: { value: ReactNode; label: ReactNode; help?: ReactNode }) {
  return (
    <div className="feed-stat">
      <span className="feed-stat__value">{value}</span>
      <span className="feed-stat__label">
        {label}
        {help && <b className="govuk-!-font-size-16 bods-relative-bottom">{help}</b>}
      </span>
    </div>
  );
}

function UseApiBlock() {
  return (
    <>
      <hr className="govuk-section-break govuk-section-break--m govuk-section-break--visible" />
      <h3 className="govuk-heading-m govuk-!-margin-top-7">Use API</h3>
      <p className="govuk-body-m">
        <a className="govuk-link" href={dataPath('/account/signup/')}>
          Register
        </a>
        {' or '}
        <a className="govuk-link" href={dataPath('/account/login/')}>
          sign in
        </a>
        {" to use this operator's data."}
      </p>
    </>
  );
}

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

function CompleteServicePagesLayout({ operator }: { operator: OperatorDetail }) {
  const { flags } = operator;
  const id = operator.id;
  return (
    <>
      <h1 className="govuk-heading-l">{operator.shortName}</h1>
      <ul className="govuk-list">
        <li className="govuk-!-margin-bottom-5">
          <a className="govuk-link" href={operatorPublishUrl(id, 'data-activity')}>
            Review consumer activity and feedback
          </a>
        </li>
      </ul>
      <p className="govuk-body">
        The service codes summarised here are registered with the OTC and are in scope of BODS, but are not yet
        published in a complete and accurate way.
      </p>
      <p className="govuk-body govuk-!-margin-bottom-5">
        Please work with your technology suppliers to provide accurate data so that consumers and your passengers can
        benefit.
      </p>
      <div id="feed-stat-list" className="govuk-grid-row govuk-!-margin-bottom-1">
        <div className="govuk-grid-column-one-half">
          <ComplianceTag compliant={operator.totalServicesRequiringAttention === 0} />
        </div>
      </div>
      <div id="feed-stat-list" className="govuk-grid-row">
        <div className="govuk-grid-column-two-thirds">
          <div className="feed-stat">
            <span className="feed-stat__value csp-inline">{djangoValue(operator.totalServicesRequiringAttention)}</span>
            <span className="csp-total-inscope-inseason">/{djangoValue(operator.totalInScopeInSeasonServices)}</span>
            <span className="feed-stat__label">
              Total services that require attention
              <b className="govuk-!-font-size-16 bods-relative-bottom">
                <OverallRequireAttentionHelp />
              </b>
            </span>
          </div>
        </div>
      </div>
      <ul className="govuk-list govuk-!-margin-top-5">
        <li>
          {flags.isAvlRequireAttentionActive ? (
            <a className="govuk-link" href={operatorPublishUrl(id, 'compliance-report')}>
              Download compliance report
            </a>
          ) : (
            <a className="govuk-link" href={operatorPublishUrl(id, 'service-codes')}>
              Download detailed export
            </a>
          )}
        </li>
      </ul>
      <hr className="govuk-section-break govuk-section-break--m govuk-section-break--visible" />
      <table className="govuk-table">
        <caption className="govuk-table__caption">
          <h3 className="govuk-heading-m">Review data accuracy</h3>
          <p className="govuk-body">
            The complete service pages here provide a combined view of real time location data, timetables and fares
            data.
            <br />
            <br />
            Please review the data for each service and supply feedback if any issues exist.
          </p>
        </caption>
        <tbody className="govuk-table__body">
          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              <LicenceAccordion>
                <ul className="govuk-list govuk-!-margin-bottom-1 licence-list">
                  {operator.operatorLicences.map((licence) => (
                    <li className="govuk-!-margin-bottom-1" key={licence.licenceNumber}>
                      <LicenceComplianceHelp nonCompliant={licence.nonCompliant} />
                      <a className="govuk-link" href={operatorLicenceUrl(licence.licenceNumber, id)}>
                        {licence.licenceNumber}: {licence.operatorName}
                      </a>
                    </li>
                  ))}
                </ul>
              </LicenceAccordion>
            </th>
          </tr>
        </tbody>
      </table>

      <h3 className="govuk-heading-m govuk-!-margin-top-3">
        Timetables data{' '}
        <ComplianceTag
          compliant={operator.timetableServicesRequiringAttentionCount === 0}
          className="govuk-!-margin-left-1"
        />
      </h3>
      <div id="feed-stat-list" className="govuk-grid-row">
        <div className="govuk-grid-column-one-half">
          <FeedStat
            value={djangoValue(operator.timetableServicesRequiringAttentionCount)}
            label="Services requiring attention"
            help={<TimetableRequireAttentionHelp />}
          />
        </div>
      </div>
      <ul className="govuk-list govuk-!-margin-top-5">
        <li className="govuk-!-margin-bottom-3">
          <a className="govuk-link" href={operatorBrowseUrl(id, 'timetable')}>
            Browse Timetables data
          </a>
        </li>
      </ul>
      {operator.isAuthenticated && (
        <FeedUrlPanel label="Timetables data API feed URL" id="timetable-feed-url" url={operator.timetableFeedUrl ?? ''} />
      )}

      <hr className="govuk-section-break govuk-section-break--l govuk-section-break--visible" />
      <h3 className="govuk-heading-m govuk-!-margin-top-7">
        Location data{' '}
        <ComplianceTag
          compliant={operator.avlServicesRequiringAttentionCount === 0}
          className="govuk-!-margin-left-1"
        />
      </h3>
      <div id="feed-stat-list" className="govuk-grid-row">
        {flags.isAvlRequireAttentionActive && (
          <div className="govuk-grid-column-one-half">
            <FeedStat
              value={djangoValue(operator.avlServicesRequiringAttentionCount)}
              label="Services requiring attention"
              help={<AvlRequireAttentionHelp />}
            />
          </div>
        )}
      </div>
      <ul className="govuk-list govuk-!-margin-top-5">
        <li>
          <a className="govuk-link" href={operatorPublishUrl(id, 'ppc-archive')}>
            Download matching report
          </a>
        </li>
        <li className="govuk-!-margin-bottom-3">
          <a className="govuk-link" href={operatorBrowseUrl(id, 'avl')}>
            Browse Location data
          </a>
        </li>
      </ul>
      {operator.isAuthenticated && (
        <FeedUrlPanel label="SIRI-VM - Location data API feed URL" id="avl-feed-url" url={operator.avlFeedUrl ?? ''} />
      )}

      <hr className="govuk-section-break govuk-section-break--l govuk-section-break--visible" />
      <h3 className="govuk-heading-m govuk-!-margin-top-7">
        Fares data{' '}
        <ComplianceTag
          compliant={operator.faresServicesRequiringAttentionCount === 0}
          className="govuk-!-margin-left-1"
        />
      </h3>
      <div id="feed-stat-list" className="govuk-grid-row">
        <div className="govuk-grid-column-one-half">
          <FeedStat
            value={djangoValue(operator.faresServicesRequiringAttentionCount)}
            label="Services requiring attention"
            help={<FaresRequireAttentionHelp />}
          />
        </div>
      </div>
      <ul className="govuk-list govuk-!-margin-top-5">
        <li className="govuk-!-margin-bottom-3">
          <a className="govuk-link" href={operatorBrowseUrl(id, 'fares')}>
            Browse Fares data
          </a>
        </li>
      </ul>
      {operator.isAuthenticated && (
        <FeedUrlPanel label="Fares data API feed URL" id="fares-feed-url" url={operator.faresFeedUrl ?? ''} />
      )}
      {!operator.isAuthenticated && <UseApiBlock />}
    </>
  );
}

function LegacyLayout({ operator }: { operator: OperatorDetail }) {
  const { flags } = operator;
  const id = operator.id;
  return (
    <>
      <h1 className="govuk-heading-l">{operator.shortName}</h1>
      <ul className="govuk-list">
        <li className="govuk-!-margin-bottom-3">
          <a className="govuk-link" href={operatorContactUrl(id)}>
            Contact {operator.shortName}
          </a>
        </li>
        <li className="govuk-!-margin-bottom-3">
          <a className="govuk-link" href={dataPath('/downloads/')}>
            Download all data
          </a>
        </li>
        <li className="govuk-!-margin-bottom-5">
          <a className="govuk-link" href={operatorPublishUrl(id, 'data-activity')}>
            Consumer activity
          </a>
        </li>
      </ul>
      <hr className="govuk-section-break govuk-section-break--m govuk-section-break--visible" />
      <table className="govuk-table">
        <caption className="govuk-table__caption">
          <h3 className="govuk-heading-m">Organisation detail</h3>
        </caption>
        <tbody className="govuk-table__body">
          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Long name
            </th>
            <td className="govuk-table__cell" colSpan={2}>
              {operator.name}
            </td>
          </tr>
          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Date registered
            </th>
            <td className="govuk-table__cell" colSpan={2}>
              {formatOperatorDate(operator.created)}
            </td>
          </tr>
          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Licence number
            </th>
            <td className="govuk-table__cell" colSpan={2}>
              <ul className="govuk-list govuk-!-margin-bottom-0">
                {operator.licenceNumbers.map((number) => (
                  <li className="govuk-!-margin-bottom-1" key={number}>
                    {number}
                  </li>
                ))}
              </ul>
            </td>
          </tr>
          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              National Operator Code
            </th>
            <td className="govuk-table__cell" colSpan={2}>
              <ul className="govuk-list govuk-!-margin-bottom-0">
                {operator.nocs.map((noc) => (
                  <li className="govuk-!-margin-bottom-1" key={noc}>
                    {noc}
                  </li>
                ))}
              </ul>
            </td>
          </tr>
        </tbody>
      </table>

      <h3 className="govuk-heading-m govuk-!-margin-top-3">
        Timetables data <ComplianceTag compliant={operator.servicesRequireAttentionPercentage === 0} />
      </h3>
      <p className="govuk-body">
        The service codes summarised here are registered with the OTC and are in scope of BODS, but are not yet
        published in a complete and accurate way.
      </p>
      <p className="govuk-body">
        Please download the detailed export for more information on the compliance data relating to each service.
      </p>
      <p className="govuk-body">Please contact the service desk if you have any questions or require any support.</p>
      <div id="feed-stat-list" className="govuk-grid-row">
        <div className="govuk-grid-column-one-half">
          <FeedStat
            value={djangoValue(operator.totalInScopeInSeasonServices)}
            label={
              <>
                Total in scope/in season
                <br />
                registered services
              </>
            }
          />
        </div>
        <div className="govuk-grid-column-one-half">
          <FeedStat
            value={`${djangoValue(operator.servicesRequireAttentionPercentage)}%`}
            label="Services requiring attention"
          />
        </div>
      </div>
      <ul className="govuk-list govuk-!-margin-top-5">
        <li>
          <a
            className="govuk-link"
            href={operatorPublishUrl(id, flags.isAvlRequireAttentionActive ? 'compliance-report' : 'service-codes')}
          >
            Download detailed export
          </a>
        </li>
        <li className="govuk-!-margin-bottom-3">
          <a className="govuk-link" href={operatorBrowseUrl(id, 'timetable')}>
            Browse Timetables data
          </a>
        </li>
      </ul>
      {operator.isAuthenticated && (
        <FeedUrlPanel label="Timetables data API feed URL" id="timetable-feed-url" url={operator.timetableFeedUrl ?? ''} />
      )}

      <hr className="govuk-section-break govuk-section-break--l govuk-section-break--visible" />
      <h3 className="govuk-heading-m govuk-!-margin-top-7">Location data</h3>
      <p className="govuk-body">
        The AVL to Timetables feed matching is a weekly score of a published data feed. Daily random samples of data
        packets are collected for each published feed to be matched and then collated together to create a weekly
        report along with a weekly associated summary score for that report. This is usually done on Monday every
        week.
      </p>
      <p className="govuk-body">This is the latest matching score for this feed.</p>
      <p className="govuk-body">
        Please note that BODS doesn&apos;t check every single packet of data but we do a random sampling throughout the
        day in order to determine these reports and scores.
      </p>
      <p className="govuk-body">
        Please download the report and work with your technology suppliers to provide the most accurate data so that
        download data consumers and eventually your bus passengers can benefit.
      </p>
      <div id="feed-stat-list" className="govuk-grid-row">
        <div className="govuk-grid-column-one-half">
          {operator.overallPpcScore !== null ? (
            <FeedStat
              value={`${operator.overallPpcScore}%`}
              label="Weekly overall AVL to timetables matching score"
            />
          ) : (
            <div className="feed-stat">
              <div>
                <span className="feed-stat__value">Pending</span>
              </div>
              <p className="feed-stat__label">Weekly overall AVL to timetables matching score</p>
            </div>
          )}
        </div>
        {flags.isAvlRequireAttentionActive && (
          <div className="govuk-grid-column-one-half">
            <FeedStat
              value={`${djangoValue(operator.avlServicesRequireAttentionPercentage)}%`}
              label="Services requiring attention"
            />
          </div>
        )}
      </div>
      <ul className="govuk-list govuk-!-margin-top-5">
        <li>
          <a className="govuk-link" href={operatorPublishUrl(id, 'ppc-archive')}>
            Download matching report
          </a>
        </li>
        <li>
          <a className="govuk-link" href={operatorBrowseUrl(id, 'avl')}>
            Browse Location data
          </a>
        </li>
        {flags.isAvlRequireAttentionActive && (
          <li className="govuk-!-margin-bottom-3">
            <a className="govuk-link" href={operatorPublishUrl(id, 'compliance-report')}>
              Download detailed export
            </a>
          </li>
        )}
      </ul>
      {operator.isAuthenticated && (
        <FeedUrlPanel label="SIRI-VM - Location data API feed URL" id="avl-feed-url" url={operator.avlFeedUrl ?? ''} />
      )}

      <hr className="govuk-section-break govuk-section-break--l govuk-section-break--visible" />
      <h3 className="govuk-heading-m govuk-!-margin-top-7">Fares data</h3>
      {!flags.isFaresRequireAttentionActive && (
        <div id="feed-stat-list" className="govuk-grid-row">
          <div className="govuk-grid-column-one-quarter">
            <FeedStat value={djangoValue(operator.faresStats?.totalDatasetCount)} label="Data sets" />
          </div>
          <div className="govuk-grid-column-one-quarter">
            <FeedStat
              value={djangoValue(operator.faresStats?.totalFareProducts)}
              label="Total number of fares products"
            />
          </div>
          <div className="govuk-grid-column-one-half">
            <FeedStat value={djangoValue(operator.faresNonCompliant)} label="Non-compliant" />
            <div className="govuk-!-margin-top-2">
              <a
                className="govuk-link"
                target="_blank"
                rel="noopener noreferrer"
                href={operatorGuidanceDataQualityUrl()}
              >
                <FontAwesomeIcon icon={faPlay} className="govuk-!-margin-right-1" />
                What does this mean?
              </a>
            </div>
          </div>
        </div>
      )}
      {flags.isFaresRequireAttentionActive && (
        <div id="attention-section" className="govuk-grid-row">
          <div className="govuk-grid-column-one-half">
            <FeedStat
              value={`${djangoValue(operator.faresServicesRequireAttentionPercentage)}%`}
              label="Services requiring attention"
            />
          </div>
        </div>
      )}
      <div id="browse-section" className="govuk-grid-row">
        <div className="govuk-grid-column-one-half">
          <ul className="govuk-list govuk-!-margin-top-5">
            <li>
              <a className="govuk-link" href={operatorBrowseUrl(id, 'fares')}>
                Browse Fares data
              </a>
            </li>
            {flags.isFaresRequireAttentionActive && (
              <li className="govuk-!-margin-bottom-3">
                <a className="govuk-link" href={operatorPublishUrl(id, 'compliance-report')}>
                  Download detailed export
                </a>
              </li>
            )}
          </ul>
        </div>
      </div>
      {operator.isAuthenticated && (
        <FeedUrlPanel label="Fares data API feed URL" id="fares-feed-url" url={operator.faresFeedUrl ?? ''} />
      )}
      {!operator.isAuthenticated && <UseApiBlock />}
    </>
  );
}

export function OperatorDetailContent({ operatorId }: OperatorDetailContentProps) {
  const [operator, setOperator] = useState<OperatorDetail | null>(null);
  const [error, setError] = useState('');
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    document.title = 'Operator details';
  }, []);

  useEffect(() => {
    let cancelled = false;
    api
      .get<OperatorDetail>(operatorDetailApiPath(operatorId))
      .then((response) => {
        if (!cancelled) setOperator(response);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) {
          setMissing(true);
          return;
        }
        setError('Failed to load operator');
      });
    return () => {
      cancelled = true;
    };
  }, [operatorId]);

  if (missing) notFound();

  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={hostBreadcrumbs('data', { label: 'Operator Profiles', href: operatorsListUrl() }, ...(operator
          ? [
              {
                label: truncateChars(operator.shortName, 19),
                href: operatorDetailUrl(operatorId),
                current: true,
              },
            ]
          : []))}
      />
      <div className="govuk-main-wrapper">
        {error && <ErrorDisplay message={error} />}
        {!operator && !error && <LoadingSpinner message="Loading operator" />}
        {operator && (
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-two-thirds">
              {operator.flags.isCompleteServicePagesActive ? (
                <CompleteServicePagesLayout operator={operator} />
              ) : (
                <LegacyLayout operator={operator} />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
