'use client';

import { useState, type ReactNode } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCircleQuestion } from '@fortawesome/free-solid-svg-icons';
import { Breadcrumbs, type BreadcrumbItem } from '@/components/shared/Breadcrumbs';
import { publishAppPath } from '@/config/client';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';

export interface SeasonalServiceOrganisation {
  organisationId: number;
  organisationName: string;
  isAgentUser: boolean;
}

export interface SeasonalServiceRow {
  id: number;
  licenceNumber: string;
  registrationCode: number;
  serviceCode: string;
  start: string;
  end: string;
  serviceBegins: string;
  serviceEnds: string;
}

export const SEASONAL_SERVICE_HEADING = 'Seasonal service operating dates';

export function seasonalServicesApiPath(orgId: string, suffix = ''): string {
  return `/api/publish/seasonal-services/${encodeURIComponent(orgId)}/${suffix}`;
}

export function reviewTimetablesPath(orgId: string): string {
  return publishAppPath(`/org/${orgId}/dataset/timetable/`);
}

export function seasonalServicesListPath(orgId: string): string {
  return publishAppPath(`/org/${orgId}/dataset/timetable/seasonal-service/`);
}

export function addNewPath(orgId: string): string {
  return publishAppPath(`/org/${orgId}/dataset/timetable/seasonal-service/add-new`);
}

/** Django keeps the list page through the journey as `?page=<n>&`, blank when absent. */
export function pageQuery(page: string | null | undefined): string {
  return `?page=${page ?? ''}&`;
}

/** Mirrors Django's `title` template filter (used for the agent breadcrumb). */
export function djangoTitle(value: string): string {
  const titled = value.replace(/[A-Za-z]+/g, (word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase());
  return titled.replace(/([a-z])'([A-Z])/g, (match) => match.toLowerCase());
}

interface SeasonalServiceBreadcrumbsProps {
  orgId: string;
  organisation: SeasonalServiceOrganisation;
  extra?: BreadcrumbItem;
  stepper?: ReactNode;
}

export function SeasonalServiceBreadcrumbs({ orgId, organisation, extra, stepper }: SeasonalServiceBreadcrumbsProps) {
  const reviewLabel = organisation.isAgentUser
    ? `${djangoTitle(`Review ${organisation.organisationName}`)} Timetables Data`
    : 'Review My Timetables Data';

  const items = hostBreadcrumbs(
    'publish',
    { label: reviewLabel, href: reviewTimetablesPath(orgId) },
    { label: 'Manage seasonal services', href: seasonalServicesListPath(orgId) },
    ...(extra ? [extra] : []),
  );

  return (
    <div className="govuk-width-container">
      <Breadcrumbs items={items} />
      {stepper}
    </div>
  );
}

export function OperatingDatesHelpModal() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="help-modal">
      <FontAwesomeIcon
        icon={faCircleQuestion}
        className="help-icon"
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            setIsOpen(!isOpen);
          }
        }}
        role="button"
        tabIndex={0}
        aria-label="Help"
      />
      <div className={`overlay ${isOpen ? 'active' : ''}`}>
        <div className="window">
          <button type="button" className="close-button govuk-link" onClick={() => setIsOpen(false)}>
            Close
          </button>
          <div className="content">
            <h1 className="govuk-heading-m">Service operating dates</h1>
            <p className="govuk-body">Use the date range to mark when this service intends to operate.</p>
            <ul className="govuk-list">
              <li>
                <b>Example 1:</b>{' '}
                For example with school services, mark the date the service begins on at the start of the autumn term
                and enter the date the service ends on as the last day of the summer term.
              </li>
              <li>
                <b>Example 2:</b>{' '}
                For a Christmas service, mark the date the service starts for the Christmas period and enter the date
                the service ends.
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

interface DateFieldsProps {
  idPrefix: string;
  values: { start: string; end: string };
  errors: { start?: string; end?: string };
  onChange: (field: 'start' | 'end', value: string) => void;
  startName?: string;
  endName?: string;
}

/** "Service begins on" / "Service ends on" pair; one error bar on the container, as Django's `DateDiv`. */
export function DateFields({ idPrefix, values, errors, onChange, startName = 'start', endName = 'end' }: DateFieldsProps) {
  const hasError = Boolean(errors.start || errors.end);
  const startId = `id_${idPrefix}start`;
  const endId = `id_${idPrefix}end`;

  return (
    <div className={`date-container${hasError ? ' govuk-form-group--error' : ''}`}>
      <div className="date">
        <label className="govuk-label" htmlFor={startId}>
          Service begins on
        </label>
        {errors.start && (
          <span id={`1_${startId}-error`} className="govuk-error-message">
            {errors.start}
          </span>
        )}
        <input
          type="date"
          required
          name={startName}
          className={`govuk-input${errors.start ? ' govuk-input--error' : ''}`}
          id={startId}
          value={values.start}
          onChange={(event) => onChange('start', event.target.value)}
        />
      </div>
      <div className="date">
        <label className="govuk-label" htmlFor={endId}>
          Service ends on
        </label>
        {errors.end && (
          <span id={`1_${endId}-error`} className="govuk-error-message">
            {errors.end}
          </span>
        )}
        <input
          type="date"
          required
          name={endName}
          className={`govuk-input${errors.end ? ' govuk-input--error' : ''}`}
          id={endId}
          value={values.end}
          onChange={(event) => onChange('end', event.target.value)}
        />
      </div>
    </div>
  );
}

export function OperatingDatesHeading() {
  return (
    <h2 className="govuk-heading-s">
      Service operating dates <OperatingDatesHelpModal />
    </h2>
  );
}
