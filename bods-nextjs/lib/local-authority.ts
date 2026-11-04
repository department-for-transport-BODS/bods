/**
 * Types and helpers shared by the Local Transport Authority pages (data host).
 *
 * Source: transit_odp/browse/views/api.py
 * Django views: transit_odp/browse/views/local_authority.py
 */

import { dataPath } from '@/config/client';
import { dataApiPath } from '@/lib/api-paths';

export const LOCAL_AUTHORITY_LIST_API_PATH = dataApiPath('/api/browser/local-authority/');
export const LOCAL_AUTHORITY_DETAIL_API_PATH = dataApiPath('/api/browser/local-authority/detail/');

export const DEFAULT_LTA_ORDERING = 'ui_lta_name_trimmed';

export interface LocalAuthorityListItem {
  name: string;
  /** Ids of the LocalAuthority rows behind this UI LTA, passed on as `auth_ids`. */
  authIds: number[];
  servicesRequireAttentionPercentage: number;
}

export interface LocalAuthorityListResponse {
  q: string;
  ordering: string;
  count: number;
  page: number;
  numPages: number;
  pageSize: number;
  /** Django's `paginator_range` output: page numbers with "..." gaps. */
  pageRange: Array<number | string>;
  results: LocalAuthorityListItem[];
  /** Every UI LTA name, for the search autocomplete. */
  names: string[];
}

export interface LocalAuthorityLicence {
  licenceNumber: string;
  operatorName: string;
  licenceOrganisationId: number | null;
  nonCompliant: boolean;
}

export interface LocalAuthorityDetail {
  name: string;
  authIds: string;
  isCompleteServicePagesActive: boolean;
  isAvlRequireAttentionActive: boolean;
  isFaresRequireAttentionActive: boolean;
  totalInScopeInSeasonServices: number;
  servicesRequireAttentionPercentage: number;
  totalTimetableRecordsRequiringAttention: number;
  /** The following are only set when complete service pages are active. */
  totalServicesRequiringAttention: number | null;
  totalLocationRecordsRequiringAttention: number | null;
  totalFaresRecordsRequiringAttention: number | null;
  licences: LocalAuthorityLicence[];
}

/** Mirrors Django's accepted `auth_ids` formats: `1,2` or `[1, 2]`. */
export function isValidAuthIds(value: string | null): value is string {
  return value !== null && /^\[?\s*\d+(\s*,\s*\d+)*\s*\]?$/.test(value);
}

/** Django renders the python list, e.g. `[1, 2]`, into the `auth_ids` query param. */
export function formatAuthIds(authIds: number[]): string {
  return `[${authIds.join(', ')}]`;
}

function withAuthIds(path: string, authIds: string): string {
  return `${path}?auth_ids=${encodeURIComponent(authIds)}`;
}

export function localAuthorityDetailUrl(authIds: string): string {
  return withAuthIds(dataPath('/local-authority/detail'), authIds);
}

export function localAuthorityExportUrls(authIds: string) {
  return {
    complianceReport: withAuthIds(dataPath('/local-authority/compliance-report'), authIds),
    detailedExport: withAuthIds(dataPath('/local-authority/export'), authIds),
    lineLevelExport: withAuthIds(dataPath('/local-authority/line-level-export'), authIds),
  };
}

/**
 * Django: `operator-licence-detail` plus `?org_id=`. The licence pages are migrated in a
 * separate branch. `org_id` is omitted when the licence has no organisation (Django would
 * render the literal `<NA>`).
 */
export function licenceDetailUrl(licenceNumber: string, organisationId: number | null): string {
  const base = dataPath(`/operators/licence/${encodeURIComponent(licenceNumber)}/`);
  return organisationId === null ? base : `${base}?org_id=${organisationId}`;
}

/** Django's `truncatechars`: keeps `length` characters including the "…" it appends. */
export function truncateChars(value: string, length: number): string {
  return value.length > length ? `${value.slice(0, Math.max(length - 1, 0))}…` : value;
}
