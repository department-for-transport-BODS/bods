'use client';

/**
 * Operator Licence details (data host, `/operators/licence/<number>/`)
 *
 * Source: transit_odp/browse/templates/browse/operators/licence_details.html
 * Behaviour: transit_odp/frontend/assets/js/licence-details.js (filters, sorting, map refresh)
 * View: transit_odp/browse/views/operators.py - LicenceDetailView
 * API: transit_odp/browse/views/operators_api.py - licence_detail_api
 *
 * Django ignores `?org_id=` (the view reads it from URL kwargs, which the URLconf never
 * supplies), so this page does too.
 */

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSortDown, faSortUp } from '@fortawesome/free-solid-svg-icons';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { MapboxRouteMap } from '@/components/data/MapboxRouteMap';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorDisplay } from '@/components/shared/ErrorDisplay';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { dataPath, wwwPath } from '@/config/client';
import { ApiError, api } from '@/lib/api-client';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';
import {
  djangoValue,
  operatorBrowseUrl,
  operatorDetailUrl,
  operatorLicenceApiPath,
  operatorLicenceLineUrl,
  operatorLicenceUrl,
  operatorsListUrl,
  truncateChars,
  type LicenceDetail,
  type LicenceService,
} from '@/lib/operators';
import {
  initialFilters,
  mapRegistrationNumber,
  matchesFilters,
  sortServices,
  type LicenceFilters,
} from './licence-services';

interface LicenceDetailContentProps {
  licenceNumber: string;
}

function toggleValue<T>(values: T[], value: T): T[] {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

function Checkbox({
  id,
  name,
  value,
  label,
  checked,
  onChange,
}: {
  id: string;
  name: string;
  value: string | number;
  label: string;
  checked: boolean;
  onChange: () => void;
}) {
  return (
    <div className="govuk-checkboxes__item">
      <input
        className="govuk-checkboxes__input licence-filter"
        id={id}
        name={name}
        type="checkbox"
        value={value}
        checked={checked}
        onChange={onChange}
      />
      <label className="govuk-label govuk-checkboxes__label" htmlFor={id}>
        {label}
      </label>
    </div>
  );
}

function FilterTable({
  licence,
  filters,
  onChange,
}: {
  licence: LicenceDetail;
  filters: LicenceFilters;
  onChange: (filters: LicenceFilters) => void;
}) {
  return (
    <table className="govuk-table">
      <caption className="govuk-table__caption govuk-table__caption--m">Filter services by</caption>
      <thead className="govuk-table__head">
        <tr>
          <th scope="col" className="govuk-table__header">
            Local transport authority
          </th>
          <th scope="col" className="govuk-table__header">
            Scope/Seasonality
          </th>
          {licence.hasFranchise && (
            <>
              <th scope="col" className="govuk-table__header">
                Franchise
              </th>
              <th scope="col" className="govuk-table__header">
                Operator
              </th>
            </>
          )}
        </tr>
      </thead>
      <tbody className="govuk-table__body">
        <tr className="govuk-table__row">
          <td className="govuk-table__cell">
            {licence.localAuthorities.map((authority) => (
              <Checkbox
                key={authority.id}
                id={`lta_${authority.id}`}
                name="lta_details"
                value={authority.id}
                label={authority.name}
                checked={filters.ltas.includes(String(authority.id))}
                onChange={() => onChange({ ...filters, ltas: toggleValue(filters.ltas, String(authority.id)) })}
              />
            ))}
            {licence.hasNullLocalAuthority && (
              <Checkbox
                id="lta_blank"
                name="lta_details"
                value="blank"
                label="Not Assigned"
                checked={filters.ltas.includes('blank')}
                onChange={() => onChange({ ...filters, ltas: toggleValue(filters.ltas, 'blank') })}
              />
            )}
          </td>
          <td className="govuk-table__cell">
            <Checkbox
              id="in_scope_checkbox"
              name="scope_details"
              value="service-in-scope"
              label="In Scope"
              checked={filters.inScope}
              onChange={() => onChange({ ...filters, inScope: !filters.inScope })}
            />
            <Checkbox
              id="out_of_scope_checkbox"
              name="scope_details"
              value="service-out-of-scope"
              label="Out of scope"
              checked={filters.outOfScope}
              onChange={() => onChange({ ...filters, outOfScope: !filters.outOfScope })}
            />
            <Checkbox
              id="in_season_checkbox"
              name="season_details"
              value="service-in-season"
              label="In Season"
              checked={filters.inSeason}
              onChange={() => onChange({ ...filters, inSeason: !filters.inSeason })}
            />
            <Checkbox
              id="out_of_season_checkbox"
              name="season_details"
              value="service-out-of-season"
              label="Out of season"
              checked={filters.outOfSeason}
              onChange={() => onChange({ ...filters, outOfSeason: !filters.outOfSeason })}
            />
          </td>
          {licence.hasFranchise && (
            <>
              <td className="govuk-table__cell">
                {licence.franchises.map((franchise) => (
                  <Checkbox
                    key={franchise.id}
                    id={`franchise_${franchise.id}`}
                    name="franchise_detailse"
                    value={franchise.id}
                    label={franchise.name}
                    checked={filters.franchises.includes(franchise.id)}
                    onChange={() => onChange({ ...filters, franchises: toggleValue(filters.franchises, franchise.id) })}
                  />
                ))}
              </td>
              <td className="govuk-table__cell">
                {licence.operators.map((operator) => (
                  <Checkbox
                    key={operator.id}
                    id={`operator_${operator.id}`}
                    name="operator_details"
                    value={operator.id}
                    label={operator.name}
                    checked={filters.operators.includes(operator.id)}
                    onChange={() => onChange({ ...filters, operators: toggleValue(filters.operators, operator.id) })}
                  />
                ))}
              </td>
            </>
          )}
        </tr>
      </tbody>
    </table>
  );
}

const SORTABLE_HEADINGS = ['Service Number', 'Timetable data', 'Location data', 'Fares data'];

function Dot({ red }: { red: boolean }) {
  return <span className={`sra-dot ${red ? 'sra-dot-red' : 'sra-dot-green'}`} />;
}

interface SortState {
  column: number;
  ascending: boolean;
}

function ServicesTable({
  licence,
  services,
  filters,
  sorted,
  onSort,
}: {
  licence: LicenceDetail;
  /** Already in display order. */
  services: LicenceService[];
  filters: LicenceFilters;
  sorted: SortState | null;
  onSort: (column: number) => void;
}) {
  return (
    <table className="govuk-table" id="licence-services-table">
      <thead className="govuk-table__head">
        <tr>
          {SORTABLE_HEADINGS.map((heading, column) => {
            const isSorted = sorted?.column === column;
            // Django ships column 0 with an ascending icon until a sort replaces it.
            const showIcon = sorted ? isSorted : column === 0;
            const ascending = sorted ? sorted.ascending : true;
            return (
              <th
                key={heading}
                scope="col"
                className={`govuk-table__header govuk-link sort-column${isSorted ? ' sorted' : ''}`}
                onClick={() => onSort(column)}
              >
                {heading}
                {showIcon && (
                  <>
                    {' '}
                    <FontAwesomeIcon icon={ascending ? faSortUp : faSortDown} className="sort-icon" />
                  </>
                )}
              </th>
            );
          })}
        </tr>
      </thead>
      <tbody className="govuk-table__body">
        {services.map((service) => (
          <ServiceRow
            key={`${service.registrationNumber}-${service.serviceNumber}`}
            licence={licence}
            service={service}
            hidden={!matchesFilters(service, filters)}
          />
        ))}
      </tbody>
    </table>
  );
}

function ServiceRow({
  licence,
  service,
  hidden,
}: {
  licence: LicenceDetail;
  service: LicenceService;
  hidden: boolean;
}) {
  return (
    <tr className={`govuk-table__row licence-details-service-row${hidden ? ' js-hidden' : ''}`}>
      <td className="govuk-table__cell">
        <Link
          className="govuk-link"
          href={operatorLicenceLineUrl(
            licence.licenceNumber,
            licence.organisationId,
            service.serviceNumber,
            service.registrationNumber,
          )}
        >
          {service.fullRegistrationNumber}
        </Link>
      </td>
      <td className="govuk-table__cell govuk-!-text-align-centre">
        <Dot red={service.requiresAttention} />
      </td>
      <td className="govuk-table__cell govuk-!-text-align-centre">
        <Dot red={service.avlRequiresAttention} />
      </td>
      <td className="govuk-table__cell govuk-!-text-align-centre">
        <Dot red={service.faresRequiresAttention} />
      </td>
    </tr>
  );
}

/**
 * Django's template has no `{% for %}` around this legacy (prefetch flag off) block, so it renders
 * one paragraph whose `service` variable is undefined: an empty link, an empty red tag.
 */
function LegacyServices({ licence }: { licence: LicenceDetail }) {
  return (
    <p className="govuk-body govuk-!-padding-bottom-2 border-bottom-custom">
      <Link className="govuk-link" href={operatorLicenceLineUrl(licence.licenceNumber, licence.organisationId, '', '')}>
        {' - '}
      </Link>
      <span className="govuk-tag govuk-!-margin-left-2 govuk-tag--red govuk-!-font-size-16 govuk-!-text-align-centre" />
    </p>
  );
}

export function LicenceDetailContent({ licenceNumber }: LicenceDetailContentProps) {
  const [licence, setLicence] = useState<LicenceDetail | null>(null);
  const [error, setError] = useState('');
  const [missing, setMissing] = useState(false);
  const [filters, setFilters] = useState<LicenceFilters | null>(null);
  // Django's sortDirections: column 0 starts "ascending", so its first click sorts descending.
  const [directions, setDirections] = useState<Record<number, boolean>>({ 0: true });
  const [sorted, setSorted] = useState<SortState | null>(null);

  const sortedServices = useMemo(
    () => (licence && sorted ? sortServices(licence.services, sorted.column, sorted.ascending) : (licence?.services ?? [])),
    [licence, sorted],
  );

  // The map shows what the table shows: the visible rows, in display order.
  const registrationNumbers = useMemo(
    () =>
      filters
        ? sortedServices
            .filter((service) => matchesFilters(service, filters))
            .map((service) => mapRegistrationNumber(service))
            .join(',')
        : '',
    [sortedServices, filters],
  );

  const sortBy = (column: number) => {
    const ascending = !directions[column];
    setDirections({ ...directions, [column]: ascending });
    setSorted({ column, ascending });
  };

  useEffect(() => {
    document.title = 'Operator Licence details';
  }, []);

  useEffect(() => {
    let cancelled = false;
    api
      .get<LicenceDetail>(operatorLicenceApiPath(licenceNumber))
      .then((response) => {
        if (cancelled) return;
        setLicence(response);
        setFilters(
          initialFilters(
            response.localAuthorities.map((authority) => authority.id),
            response.hasNullLocalAuthority,
            response.franchises.map((franchise) => franchise.id),
            response.operators.map((operator) => operator.id),
          ),
        );
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) {
          setMissing(true);
          return;
        }
        setError('Failed to load licence');
      });
    return () => {
      cancelled = true;
    };
  }, [licenceNumber]);

  if (missing) notFound();

  const organisationCrumb = licence
    ? [
        {
          label: truncateChars(licence.organisationName, 19),
          href: licence.organisationId ? operatorDetailUrl(licence.organisationId) : '#',
        },
        {
          label: licence.licenceNumber,
          href: operatorLicenceUrl(licence.licenceNumber, djangoValue(licence.organisationId)),
          current: true,
        },
      ]
    : [];

  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={hostBreadcrumbs('data', { label: 'Operator Profiles', href: operatorsListUrl() }, ...organisationCrumb)}
      />
      <div className="govuk-main-wrapper">
        {error && <ErrorDisplay message={error} />}
        {!licence && !error && <LoadingSpinner message="Loading licence" />}
        {licence && filters && (
          <>
            <div className="govuk-grid-row">
              <div className="govuk-grid-column-two-thirds">
                <h1 className="govuk-heading-l app-!-mb-4 dont-break-out">
                  {licence.organisationName} - {licence.licenceNumber}
                </h1>
                <p className="govuk-body app-!-mb-sm-0">Overview of the available bus open data</p>
              </div>
            </div>
            <hr className="govuk-section-break govuk-section-break--m govuk-section-break--visible" />
            <div className="govuk-grid-row">
              <div className="govuk-grid-column-two-thirds">
                {licence.isPrefetchComplianceReportActive ? (
                  <MapboxRouteMap
                    licenceNumber={licence.licenceNumber}
                    registrationNumbers={registrationNumbers}
                    containerClassName=""
                    ariaLabel={`Interactive map showing the routes of licence ${licence.licenceNumber}`}
                  />
                ) : (
                  <div id="map" className="disruptions-width" />
                )}
                <table className="govuk-table consumer-property-table">
                  <tbody className="govuk-table__body">
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">
                        Owner
                      </th>
                      <td colSpan={2} className="govuk-table__cell dont-break-out">
                        <div className="stacked">
                          <a
                            className="govuk-link"
                            href={licence.organisationId ? operatorBrowseUrl(licence.organisationId, 'timetable') : '#'}
                          >
                            {licence.organisationName}
                          </a>{' '}
                          Access all data uploaded by this publisher
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
                <div className="govuk-!-margin-top-5">
                  <h2 className="govuk-heading-l">Review Service Numbers</h2>
                  {licence.isPrefetchComplianceReportActive && (
                    <FilterTable licence={licence} filters={filters} onChange={setFilters} />
                  )}
                  <div className="govuk-accordion" id="accordion-default">
                    {licence.services.length ? (
                      licence.isPrefetchComplianceReportActive ? (
                        <ServicesTable
                          licence={licence}
                          services={sortedServices}
                          filters={filters}
                          sorted={sorted}
                          onSort={sortBy}
                        />
                      ) : (
                        <LegacyServices licence={licence} />
                      )
                    ) : (
                      <span>No Services Available</span>
                    )}
                  </div>
                </div>
              </div>
              <div className="govuk-grid-column-one-third">
                <h2 className="govuk-heading-m">What you need to know</h2>
                <ul className="govuk-list app-list--nav govuk-!-font-size-19">
                  <li>
                    <Link className="govuk-link" href={dataPath('/guidance/requirements/')}>
                      View developer documentation
                    </Link>
                  </li>
                  <li>
                    <a
                      className="govuk-link"
                      href="https://www.gov.uk/government/consultations/bus-services-act-2017-bus-open-data"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Find out more about bus open data
                    </a>
                  </li>
                  <li>
                    <a className="govuk-link" href={wwwPath('/contact/')}>
                      Contact us for technical issues
                    </a>
                  </li>
                </ul>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
