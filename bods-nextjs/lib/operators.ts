/**
 * Types and helpers shared by the operator profile pages on the data host.
 *
 * Source: transit_odp/browse/views/operators_api.py
 *
 * The licence pages (`/operators/licence/<number>/...`) are built on the same
 * API surface and URL helpers, so keep them free of page-specific state.
 */

import { dataPath, publishPath } from '@/config/client';
import { dataApiPath } from '@/lib/api-paths';
import type { BookingMethods, Timetable } from '@/components/timetables/line-detail-types';

export const OPERATORS_API_PATH = dataApiPath('/api/browser/operators/');

export interface OperatorListItem {
  id: number;
  name: string;
  created: string;
}

export interface OperatorListResponse {
  q: string;
  ordering: string;
  count: number;
  page: number;
  numPages: number;
  pageSize: number;
  /** Django's `paginator_range` output: page numbers with "..." gaps. */
  pageRange: Array<number | string>;
  results: OperatorListItem[];
  operatorNames: string[];
}

export interface OperatorLicence {
  licenceNumber: string;
  operatorName: string;
  nonCompliant: boolean;
}

export interface OperatorDetail {
  id: number;
  name: string;
  shortName: string;
  created: string;
  licenceNumbers: string[];
  nocs: string[];
  isAuthenticated: boolean;
  flags: {
    isCompleteServicePagesActive: boolean;
    isAvlRequireAttentionActive: boolean;
    isFaresRequireAttentionActive: boolean;
  };
  totalInScopeInSeasonServices: number | null;
  totalServicesRequiringAttention: number | null;
  timetableServicesRequiringAttentionCount: number | null;
  avlServicesRequiringAttentionCount: number | null;
  faresServicesRequiringAttentionCount: number | null;
  servicesRequireAttentionPercentage: number | null;
  avlServicesRequireAttentionPercentage: number | null;
  faresServicesRequireAttentionPercentage: number | null;
  faresStats: { totalDatasetCount: number; totalFareProducts: number } | null;
  faresNonCompliant: number | null;
  overallPpcScore: number | null;
  operatorLicences: OperatorLicence[];
  timetableFeedUrl: string | null;
  avlFeedUrl: string | null;
  faresFeedUrl: string | null;
}

export interface OperatorContact {
  id: number;
  name: string;
}

export function operatorsApiPath(query: URLSearchParams): string {
  const queryString = query.toString();
  return queryString ? `${OPERATORS_API_PATH}?${queryString}` : OPERATORS_API_PATH;
}

export function operatorDetailApiPath(operatorId: string | number): string {
  return `${OPERATORS_API_PATH}${operatorId}/`;
}

export function operatorContactApiPath(operatorId: string | number): string {
  return `${OPERATORS_API_PATH}${operatorId}/contact/`;
}

export function operatorsListUrl(): string {
  return dataPath('/operators/');
}

/** Licence page payloads, from transit_odp/browse/views/operators_api.py (`licence_detail_api`). */
export interface LicenceService {
  serviceNumber: string;
  /** Registration number with "/" replaced by ":", as used in links and map filters. */
  registrationNumber: string;
  fullRegistrationNumber: string;
  licenceOrganisationId: number | null;
  /** Comma separated UI LTA ids; empty when the service has none. */
  localAuthorityIds: string;
  isInScope: boolean;
  isInSeason: boolean;
  requiresAttention: boolean;
  avlRequiresAttention: boolean;
  faresRequiresAttention: boolean;
  isLabelGreen: boolean;
  labelStr: string;
}

export interface LicenceDetail {
  licenceNumber: string;
  organisationId: number | null;
  organisationName: string;
  isPrefetchComplianceReportActive: boolean;
  hasFranchise: boolean;
  hasNullLocalAuthority: boolean;
  localAuthorities: Array<{ id: number; name: string }>;
  franchises: Array<{ id: number; name: string }>;
  operators: Array<{ id: number; name: string }>;
  services: LicenceService[];
}

/** `licence_line_detail_api`: the licence line page, `/operators/licence/<n>/line/details/`. */
export interface LicenceLineFile {
  filename: string;
  startDate: string | null;
  endDate: string | null;
}

export interface LicenceLineDetail {
  licenceNumber: string;
  lineName: string;
  serviceCode: string;
  /** False for the passenger facing variant (any `?pf=` value). */
  isLicencePage: boolean;
  organisation: { id: number; name: string } | null;
  datasetId: number | null;
  revisionId: number | null;
  flags: {
    isCompleteServicePagesActive: boolean;
    isCompleteServicePagesRealTimeDataActive: boolean;
    isAvlRequireAttentionActive: boolean;
    isFaresRequireAttentionActive: boolean;
    isTimetableVisualiserActive: boolean;
    isSpecificFeedback: boolean;
  };
  /** Null when the dataset has no live revision (Django never computes them then). */
  serviceInScope: boolean | null;
  serviceInSeason: boolean | null;
  isAvlCompliant: boolean | null;
  isFaresCompliant: boolean | null;
  isTimetableCompliant: boolean | null;
  serviceType: string;
  bookingArrangements: string | null;
  bookingMethods: BookingMethods | null;
  fares: {
    datasetId: number | null;
    tariffBasis: string[];
    products: string[];
    validFiles: LicenceLineFile[];
    futureDatedFiles: LicenceLineFile[];
    expiredFiles: LicenceLineFile[];
  };
  timetableFiles: {
    datasetId: number | null;
    validFiles: LicenceLineFile[];
    futureDatedFiles: LicenceLineFile[];
    expiredFiles: LicenceLineFile[];
  };
  timetable: Timetable | null;
  outboundStartAndEnd: string | null;
  realTime: { nationalOperatorCode: string; vehicleJourneyCodes: string };
}

export function operatorLicenceApiPath(licenceNumber: string): string {
  return `${OPERATORS_API_PATH}licence/${licenceNumber}/`;
}

export function operatorLicenceLineApiPath(licenceNumber: string, query: { toString(): string }): string {
  const queryString = query.toString();
  return `${OPERATORS_API_PATH}licence/${licenceNumber}/line/details/${queryString ? `?${queryString}` : ''}`;
}

/** Django `licence-line-detail` plus `?org_id=<id|None>&line=&service=` (as the templates build it). */
export function operatorLicenceLineUrl(
  licenceNumber: string,
  organisationId: number | null | undefined,
  lineName: string,
  serviceCode: string,
): string {
  return dataPath(
    `/operators/licence/${licenceNumber}/line/details/?org_id=${djangoValue(organisationId)}&line=${lineName}&service=${serviceCode}`,
  );
}

/** Live vehicle positions (Django `avldetaildatafeedapirealtime`) via the data API namespace. */
export function liveVehicleLocationApiPath(lineName: string, nationalOperatorCode: string, journeyCodes: string): string {
  return dataApiPath(
    `/api/browser/avl-feed/real-time-bus-location/?lineRef=${lineName}&operatorRef=${nationalOperatorCode}&journey_code=${journeyCodes}`,
  );
}

export function operatorDetailUrl(operatorId: string | number): string {
  return dataPath(`/operators/${operatorId}/`);
}

export function operatorContactUrl(operatorId: string | number): string {
  return dataPath(`/operators/${operatorId}/contact/`);
}

export function operatorContactSuccessUrl(operatorId: string | number): string {
  return dataPath(`/operators/${operatorId}/contact/success/`);
}

/** Django: `operator-licence-detail` plus `?org_id=`. */
export function operatorLicenceUrl(licenceNumber: string, operatorId: string | number): string {
  return dataPath(`/operators/licence/${licenceNumber}/?org_id=${operatorId}`);
}

/** Publish-host pages that still render from Django. */
export function operatorPublishUrl(
  operatorId: string | number,
  page: 'compliance-report' | 'service-codes' | 'ppc-archive' | 'data-activity',
): string {
  switch (page) {
    case 'compliance-report':
      return publishPath(`/org/${operatorId}/dataset/timetable/compliance-report/`);
    case 'service-codes':
      return publishPath(`/org/${operatorId}/dataset/timetable/service-codes/`);
    case 'ppc-archive':
      return publishPath(`/org/${operatorId}/dataset/ppc-archive/`);
    case 'data-activity':
      return publishPath(`/org/${operatorId}/dataset/data-activity/?prev=operator-detail`);
  }
}

/** Data-host browse pages, filtered to an operator's live data (Django `?organisation=<id>&status=live`). */
export function operatorBrowseUrl(operatorId: string | number, type: 'timetable' | 'avl' | 'fares'): string {
  return dataPath(`/${type}/?organisation=${operatorId}&status=live`);
}

/** Django `guidance:support-bus_operators`, data quality section. */
export function operatorGuidanceDataQualityUrl(): string {
  return publishPath('/guidance/operator-requirements/?section=dataquality');
}

/** Django's `date:"j F Y"`, rendered in the same London timezone. */
export function formatOperatorDate(isoDate: string): string {
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Europe/London',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(new Date(isoDate));
}

/** Django's `truncatechars:N`: N characters including a single "…". */
export function truncateChars(value: string, length: number): string {
  if (value.length <= length) {
    return value;
  }
  return `${value.slice(0, Math.max(length - 1, 0))}…`;
}

/** Renders a context value the way a Django template would (`None` for null). */
export function djangoValue(value: number | string | null | undefined): string {
  return value === null || value === undefined ? 'None' : String(value);
}
