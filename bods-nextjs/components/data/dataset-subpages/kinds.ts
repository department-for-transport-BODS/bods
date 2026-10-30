/**
 * The three dataset types share their sub-pages (changelog, subscription,
 * feedback). Django has one view per type (transit_odp/browse/views/
 * {timetable,avl,fares}_views.py); here one component serves all three, driven
 * by this config.
 */

export type DatasetSubpageKind = 'timetables' | 'avl' | 'fares';

interface DatasetSubpageConfig {
  /** Path segment in Django's public URLs: /<segment>/dataset/<pk>/... */
  routeSegment: 'timetable' | 'avl' | 'fares';
  /** What the Django templates call the dataset: AVL says "data feed". */
  noun: 'data set' | 'data feed';
}

export const DATASET_SUBPAGE_CONFIG: Record<DatasetSubpageKind, DatasetSubpageConfig> = {
  timetables: { routeSegment: 'timetable', noun: 'data set' },
  avl: { routeSegment: 'avl', noun: 'data feed' },
  fares: { routeSegment: 'fares', noun: 'data set' },
};

/** Dataset detail page (the changelog and subscription back link). */
export function datasetDetailHref(kind: DatasetSubpageKind, id: string): string {
  return `/${DATASET_SUBPAGE_CONFIG[kind].routeSegment}/dataset/${id}`;
}

/** Dataset sub-page, e.g. /timetable/dataset/1/subscription/success. */
export function datasetSubpageHref(kind: DatasetSubpageKind, id: string, subpage: string): string {
  return `${datasetDetailHref(kind, id)}/${subpage}`;
}

/** Same-origin Django JSON endpoint for a dataset sub-page (data host, browser/...). */
export function datasetSubpageApiPath(kind: DatasetSubpageKind, id: string, subpage: string): string {
  return `/api/data/browser/${kind}/${id}/${subpage}/`;
}
