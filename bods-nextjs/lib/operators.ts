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
