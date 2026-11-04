/**
 * Public data-host URLs for browsing datasets, mirroring Django's URLconf:
 *   transit_odp/browse/urls/{timetables,avl,fares}.py
 *
 *   /timetable/                       search            (list)
 *   /timetable/dataset/<pk>/          feed-detail       (detail)
 *   /timetable/dataset/<pk>/changelog/ ... subscription/, feedback/, download/
 *   /avl/...  and  /fares/...  follow the same shape.
 *
 * Pages that exist in Next.js are linked without a trailing slash (Next.js is
 * configured with trailingSlash: false). Sub-pages that are not ported yet keep
 * Django's exact URL (with trailing slash) so they reach the right page once
 * the Next.js frontend serves them.
 */

import { dataPath } from '@/config/client';
import type { DatasetType } from '@/types';

const TYPE_SEGMENT: Record<DatasetType, string> = {
  TIMETABLE: 'timetable',
  AVL: 'avl',
  FARES: 'fares',
};

export type DatasetSubpage = 'changelog' | 'subscription' | 'feedback' | 'download';

function toQueryString(query?: Record<string, string | number | null | undefined>): string {
  if (!query) return '';
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== null && value !== undefined && value !== '') {
      params.set(key, String(value));
    }
  }
  const text = params.toString();
  return text ? `?${text}` : '';
}

/** Dataset search page, e.g. /timetable?status=live (Django: "search", "avl-search", "search-fares"). */
export function datasetListPath(
  type: DatasetType,
  query?: Record<string, string | number | null | undefined>,
): string {
  return dataPath(`/${TYPE_SEGMENT[type]}${toQueryString(query)}`);
}

/** Dataset detail page, e.g. /timetable/dataset/1 (Django: "feed-detail", "avl-feed-detail", "fares-feed-detail"). */
export function datasetDetailPath(type: DatasetType, id: number | string): string {
  return dataPath(`/${TYPE_SEGMENT[type]}/dataset/${id}`);
}

/** Dataset sub-page (not yet ported), e.g. /timetable/dataset/1/changelog/. */
export function datasetSubpagePath(
  type: DatasetType,
  id: number | string,
  subpage: DatasetSubpage,
): string {
  return dataPath(`/${TYPE_SEGMENT[type]}/dataset/${id}/${subpage}/`);
}
