'use client';

/**
 * Operator Licence line detail (data host, `/operators/licence/<number>/line/details/`)
 *
 * Source: transit_odp/browse/templates/browse/timetables/dataset_detail/licence_review_line_metadata.html
 *         transit_odp/browse/templates/browse/base/feedback.html
 * Behaviour: transit_odp/frontend/assets/js/feed-detail-map.js (map and live vehicles)
 * View: transit_odp/browse/views/operators.py - LicenceLineMetadataDetailView
 * API: transit_odp/browse/views/operators_api.py - licence_line_detail_api
 *
 * Query parameters (`line`, `service`, `pf`, `date`, the timetable paging params) go to the API
 * unchanged. Any `pf` value selects the passenger facing variant, as in Django.
 */

import { notFound, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useMemo, useState, type ReactNode } from 'react';
import { MapboxRouteMap } from '@/components/data/MapboxRouteMap';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorDisplay } from '@/components/shared/ErrorDisplay';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { FileList, LinePropertyTable } from '@/components/timetables/LinePropertyTable';
import type { Timetable } from '@/components/timetables/line-detail-types';
import { queryWith } from '@/components/timetables/query';
import { TimetableVisualiser } from '@/components/timetables/TimetableVisualiser';
import { dataPath } from '@/config/client';
import { ApiError, api } from '@/lib/api-client';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';
import {
  djangoValue,
  liveVehicleLocationApiPath,
  operatorDetailUrl,
  operatorLicenceLineApiPath,
  operatorLicenceLineUrl,
  operatorLicenceUrl,
  operatorPublishUrl,
  operatorsListUrl,
  truncateChars,
  type LicenceLineDetail,
  type LicenceLineFile,
} from '@/lib/operators';

const NO_TIMETABLE: Timetable = { currDate: '', isTimetableInfoAvailable: false, directions: [] };

function ComplianceTag({ compliant, className }: { compliant: boolean | null; className: string }) {
  return (
    <span className={`govuk-tag ${compliant ? 'govuk-tag--green' : 'govuk-tag--red'} ${className}`}>
      {compliant ? 'Compliant' : 'Not Compliant'}
    </span>
  );
}

function FileRow({ header, files }: { header: string; files: LicenceLineFile[] }) {
  return (
    <tr className="govuk-table__row">
      <th scope="row" className="govuk-table__header">
        {header}
      </th>
      <td className="govuk-table__cell dont-break-out" colSpan={2}>
        <FileList files={files} />
      </td>
    </tr>
  );
}

function SectionTable({ children }: { children: ReactNode }) {
  return (
    <div className="govuk-grid-row">
      <div className="govuk-grid-column-two-thirds">
        <table className="govuk-table dataset-property-table">
          <tbody className="govuk-table__body">{children}</tbody>
        </table>
      </div>
    </div>
  );
}

function HeadingCell({ children }: { children: ReactNode }) {
  return (
    <th scope="row" className="govuk-table__header govuk-!-width-one-half">
      <h2 className="govuk-heading-m">{children}</h2>
    </th>
  );
}

function LicenceHeading({ line }: { line: LicenceLineDetail }) {
  if (!line.isLicencePage) {
    return (
      <h1 className="govuk-heading-xl app-!-mb-4 dont-break-out">
        {line.organisation ? line.organisation.name : 'Organisation not yet created'} : {line.lineName}
        {line.timetable?.isTimetableInfoAvailable ? <> - {djangoValue(line.outboundStartAndEnd)}</> : null}
      </h1>
    );
  }

  let tag: ReactNode;
  if (line.serviceInScope === false) {
    tag = (
      <span className="govuk-tag govuk-tag--red govuk-!-margin-left-2 govuk-!-text-align-centre">Out of Scope</span>
    );
  } else if (line.serviceInSeason === false) {
    tag = (
      <span className="govuk-tag govuk-tag--red govuk-!-margin-left-2 govuk-!-text-align-centre">Out of Season</span>
    );
  } else {
    tag = (
      <ComplianceTag
        compliant={Boolean(line.isAvlCompliant && line.isFaresCompliant && line.isTimetableCompliant)}
        className="govuk-!-margin-left-3 govuk-!-font-size-16 govuk-!-text-align-centre"
      />
    );
  }

  return (
    <>
      <h1 className="govuk-heading-xl app-!-mb-4 dont-break-out govuk-!-margin-bottom-5">
        {line.lineName} {tag}
      </h1>
      <ul className="govuk-list">
        {line.organisation && (
          <li>
            <a className="govuk-link" href={operatorPublishUrl(line.organisation.id, 'compliance-report')}>
              Download compliance report
            </a>
          </li>
        )}
      </ul>
    </>
  );
}

function ComplianceSections({ line }: { line: LicenceLineDetail }) {
  const { flags, isLicencePage } = line;
  if (!flags.isCompleteServicePagesActive) return null;

  return (
    <>
      {flags.isAvlRequireAttentionActive && isLicencePage && (
        <SectionTable>
          <tr className="govuk-table__row">
            <HeadingCell>AVL</HeadingCell>
            <td className="govuk-table__cell dont-break-out " colSpan={2}>
              <ComplianceTag compliant={line.isAvlCompliant} className="govuk-!-font-size-16 govuk-!-text-align-centre" />
            </td>
          </tr>
        </SectionTable>
      )}
      {flags.isFaresRequireAttentionActive && (
        <SectionTable>
          <tr className="govuk-table__row">
            <HeadingCell>Fares</HeadingCell>
            <td className="govuk-table__cell dont-break-out" colSpan={2}>
              {isLicencePage && (
                <>
                  <ComplianceTag
                    compliant={line.isFaresCompliant}
                    className="govuk-!-font-size-16 govuk-!-text-align-centre govuk-!-margin-right-2"
                  />
                  {line.fares.datasetId ? (
                    <a href={dataPath(`/fares/dataset/${line.fares.datasetId}/`)} target="_blank" rel="noopener noreferrer">
                      Dataset ID: {line.fares.datasetId}
                    </a>
                  ) : (
                    <span className="govuk-tag govuk-tag--red govuk-!-font-size-16 govuk-!-text-align-centre govuk-!-margin-right-2">
                      Unpublished
                    </span>
                  )}
                </>
              )}
            </td>
          </tr>
          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header govuk-!-width-one-half">
              Tariff basis
            </th>
            <td className="govuk-table__cell dont-break-out" colSpan={2}>
              {line.fares.tariffBasis.length ? line.fares.tariffBasis.join(', ') : 'N/A'}
            </td>
          </tr>
          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Products
            </th>
            <td className="govuk-table__cell dont-break-out" colSpan={2}>
              {line.fares.products.length ? line.fares.products.join(', ') : 'N/A'}
            </td>
          </tr>
          {isLicencePage && (
            <>
              <FileRow header="Current valid file(s)" files={line.fares.validFiles} />
              <FileRow header="Future dated file(s)" files={line.fares.futureDatedFiles} />
              <FileRow header="Expired file(s)" files={line.fares.expiredFiles} />
            </>
          )}
        </SectionTable>
      )}
      {isLicencePage && (
        <SectionTable>
          <tr className="govuk-table__row">
            <HeadingCell>Timetable</HeadingCell>
            <td className="govuk-table__cell dont-break-out" colSpan={2}>
              <ComplianceTag
                compliant={line.isTimetableCompliant}
                className="govuk-!-font-size-16 govuk-!-text-align-centre govuk-!-margin-right-2"
              />
              {line.datasetId ? (
                <a href={dataPath(`/timetable/dataset/${line.datasetId}/`)} target="_blank" rel="noopener noreferrer">
                  Dataset ID: {djangoValue(line.timetableFiles.datasetId)}
                </a>
              ) : (
                <span className="govuk-tag govuk-tag--red govuk-!-font-size-16 govuk-!-text-align-centre govuk-!-margin-right-2">
                  Unpublished
                </span>
              )}
            </td>
          </tr>
          <FileRow header="Current valid file(s)" files={line.timetableFiles.validFiles} />
          <FileRow header="Future dated file(s)" files={line.timetableFiles.futureDatedFiles} />
          <FileRow header="Expired file(s)" files={line.timetableFiles.expiredFiles} />
        </SectionTable>
      )}
    </>
  );
}

function FeedbackBlock({ line }: { line: LicenceLineDetail }) {
  const searchParams = useSearchParams();
  const isServiceFeedback = searchParams.has('service') && line.flags.isSpecificFeedback;
  // Django's `{% url ... as base_url %}` swallows NoReverseMatch, so there is no base without a dataset.
  const baseUrl = line.datasetId ? dataPath(`/timetable/dataset/${line.datasetId}/feedback/`) : '';

  return (
    <div className="govuk-grid-row">
      <div className="govuk-grid-column-two-thirds">
        <h2 className="govuk-heading-m">
          {isServiceFeedback ? 'Noticed issues with this service?' : 'Noticed issues with this data set?'}
        </h2>
        {isServiceFeedback ? (
          <p className="govuk-body">
            You can select a stop code or journey code above to provide feedback about that specific element, or you
            can use this link to provide general feedback about this service.
          </p>
        ) : null}
        <a
          className="govuk-link govuk-!-font-size-19"
          href={isServiceFeedback ? `${baseUrl}${queryWith(searchParams, {})}` : baseUrl}
        >
          {isServiceFeedback ? 'Provide feedback about this service' : 'Contact data set owner directly'}
        </a>
      </div>
    </div>
  );
}

function LicenceLineDetail({ licenceNumber }: { licenceNumber: string }) {
  const searchParams = useSearchParams();
  const [line, setLine] = useState<LicenceLineDetail | null>(null);
  const [error, setError] = useState('');
  const [missing, setMissing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState('-');

  const query = searchParams.toString();
  const apiPath = operatorLicenceLineApiPath(licenceNumber, query);

  useEffect(() => {
    let cancelled = false;
    api
      .get<LicenceLineDetail>(apiPath)
      .then((response) => {
        if (cancelled) return;
        setLine(response);
        setError('');
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) {
          setMissing(true);
          return;
        }
        setError('Failed to load service');
      });
    return () => {
      cancelled = true;
    };
  }, [apiPath]);

  useEffect(() => {
    if (line) document.title = line.lineName;
  }, [line]);

  const liveLocationUrl = useMemo(() => {
    if (!line?.flags.isCompleteServicePagesRealTimeDataActive) return undefined;
    const noc = line.realTime.nationalOperatorCode;
    // Django skips the live feed when every comma separated operator code is blank.
    if (noc.split(',').every((code) => code.trim() === '')) return undefined;
    return liveVehicleLocationApiPath(line.lineName, noc, line.realTime.vehicleJourneyCodes);
  }, [line]);

  if (missing) notFound();

  const organisationId = line?.organisation?.id ?? null;
  const breadcrumbs = line
    ? [
        line.organisation
          ? {
              label: truncateChars(line.organisation.name, 19),
              href: operatorDetailUrl(line.organisation.id),
            }
          : { label: 'Organisation not yet created', href: '#' },
        {
          label: line.licenceNumber,
          href: operatorLicenceUrl(line.licenceNumber, djangoValue(organisationId)),
        },
        {
          label: line.lineName,
          href: operatorLicenceLineUrl(line.licenceNumber, organisationId, line.lineName, line.serviceCode),
          current: true,
        },
      ]
    : [];

  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={hostBreadcrumbs('data', { label: 'Operator Profiles', href: operatorsListUrl() }, ...breadcrumbs)}
      />
      <div className="govuk-main-wrapper">
        {error && <ErrorDisplay message={error} />}
        {!line && !error && <LoadingSpinner message="Loading service" />}
        {line && (
          <>
            <div className="govuk-grid-row">
              <div className="govuk-grid-column-two-thirds">
                <LicenceHeading line={line} />
                <p className="govuk-body app-!-mb-sm-0">Overview of the available bus open data</p>
                <hr className="govuk-section-break govuk-section-break--l govuk-section-break--invisible" />
                <div className="position-relative">
                  <MapboxRouteMap
                    revisionId={line.revisionId ?? undefined}
                    lineName={line.lineName}
                    serviceCodes={line.serviceCode}
                    liveLocationUrl={liveLocationUrl}
                    onLiveUpdate={setLastUpdated}
                    containerClassName=""
                    ariaLabel={`Interactive map showing the route of ${line.lineName}`}
                  />
                  <span id="map-updated-timestamp">{lastUpdated}</span>
                </div>
                <LinePropertyTable
                  line={{
                    serviceType: line.serviceType,
                    serviceCode: line.serviceCode,
                    bookingArrangements: line.bookingArrangements,
                    bookingMethods: line.bookingMethods,
                  }}
                  firstHeaderClassName="govuk-!-width-one-half"
                  showRegistrationNumber={line.isLicencePage}
                  showValidFiles={false}
                  showBookingDetails={line.isLicencePage}
                />
              </div>
            </div>
            <ComplianceSections line={line} />
            {line.flags.isTimetableVisualiserActive && (
              <div className="govuk-grid-row">
                <div className="govuk-grid-column-full">
                  <TimetableVisualiser
                    timetable={line.timetable ?? NO_TIMETABLE}
                    feedbackUrl={
                      line.flags.isSpecificFeedback && line.datasetId
                        ? dataPath(`/timetable/dataset/${line.datasetId}/feedback/`)
                        : null
                    }
                    renderEmptyDirections={false}
                  />
                </div>
              </div>
            )}
            {line.isLicencePage && <FeedbackBlock line={line} />}
          </>
        )}
      </div>
    </div>
  );
}

export function LicenceLineDetailContent({ licenceNumber }: { licenceNumber: string }) {
  return (
    <Suspense fallback={null}>
      <LicenceLineDetail licenceNumber={licenceNumber} />
    </Suspense>
  );
}
