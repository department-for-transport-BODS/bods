import { publishAppPath } from '@/config/client';
import type { ReviewListKind } from './types';

export interface ReviewListKindConfig {
  kind: ReviewListKind;
  /** Segment of the Django URL: /org/<id>/dataset/<segment>/ */
  pathSegment: string;
  /** Namespace of the Django JSON endpoint: /api/<namespace>/list/<id>/ */
  apiNamespace: 'timetables' | 'avl' | 'fares';
  /** Wording used by Django for the page title, e.g. "Review my <label> data". */
  dataLabel: string;
  publishNewLabel: string;
  /** Django's `?prev=` value on the data activity link. */
  dataActivityPrev: string;
  newPath: (orgId: string) => string;
}

export const REVIEW_LIST_KINDS: Record<ReviewListKind, ReviewListKindConfig> = {
  timetable: {
    kind: 'timetable',
    pathSegment: 'timetable',
    apiNamespace: 'timetables',
    dataLabel: 'timetables',
    publishNewLabel: 'Publish new data sets',
    dataActivityPrev: 'feed-list',
    newPath: (orgId) => `/org/${orgId}/dataset/timetable/new`,
  },
  avl: {
    kind: 'avl',
    pathSegment: 'avl',
    apiNamespace: 'avl',
    dataLabel: 'bus location',
    publishNewLabel: 'Publish new data feeds',
    dataActivityPrev: 'avl-feed-list',
    newPath: (orgId) => `/org/${orgId}/dataset/avl/new`,
  },
  fares: {
    kind: 'fares',
    pathSegment: 'fares',
    apiNamespace: 'fares',
    dataLabel: 'fares',
    publishNewLabel: 'Publish new data sets',
    dataActivityPrev: 'fares-feed-list',
    newPath: (orgId) => `/org/${orgId}/dataset/fares/new`,
  },
};

export const DATA_TYPE_OPTIONS: { kind: ReviewListKind; label: string; qa: string }[] = [
  { kind: 'timetable', label: 'Timetables data', qa: 'timetable-option' },
  { kind: 'avl', label: 'Bus location data', qa: 'avl-option' },
  { kind: 'fares', label: 'Fares data', qa: 'fares-option' },
];

export const TABS: { section: 'active' | 'draft' | 'archive'; title: string }[] = [
  { section: 'active', title: 'Active' },
  { section: 'draft', title: 'Draft' },
  { section: 'archive', title: 'Inactive' },
];

export function reviewListPath(orgId: string, kind: ReviewListKind): string {
  return `/org/${orgId}/dataset/${REVIEW_LIST_KINDS[kind].pathSegment}`;
}

export function reviewListUrl(orgId: string, kind: ReviewListKind): string {
  return publishAppPath(reviewListPath(orgId, kind));
}

export function datasetPath(orgId: string, kind: ReviewListKind, datasetId: number): string {
  return `${reviewListPath(orgId, kind)}/${datasetId}`;
}

/**
 * Mirrors Django's `title` template filter, which Django applies to the page
 * title for the last breadcrumb ("Review My Timetables Data").
 */
export function djangoTitle(value: string): string {
  const titled = value
    .toLowerCase()
    .replace(/\p{L}+/gu, (word) => word.charAt(0).toUpperCase() + word.slice(1))
    .replace(/([a-z])'([A-Z])/g, (match) => match.toLowerCase());

  return titled.replace(/\d([A-Z])/g, (match) => match.toLowerCase());
}
