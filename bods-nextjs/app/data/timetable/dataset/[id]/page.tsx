/**
 * Timetable Dataset Detail Page
 *
 * Public URL: /timetable/dataset/<pk>/ (Django "feed-detail"). The page is
 * public, like Django's: anonymous users see everything except the API URL
 * panel, which needs their API key.
 * The AVL and fares detail pages live in ../../../avl and ../../../fares.
 *
 * Source: transit_odp/browse/templates/browse/timetables/dataset_detail/index.html
 * View: transit_odp/browse/views/timetable_views.py - DatasetDetailView
 * API: transit_odp/timetables/views/dataset_detail_api.py - get_browse_timetable_detail_api
 *
 * Server Component: the dataset is fetched on the server with the visitor's
 * session cookie, so an unknown / hidden / wrong-type id is a real HTTP 404.
 */

import { cache } from 'react';
import { notFound } from 'next/navigation';
import { connection } from 'next/server';
import { TimetableDatasetDetailContent } from '@/components/data/dataset-detail/TimetableDatasetDetailContent';
import type { TimetableDatasetDetail } from '@/components/data/dataset-detail/types';
import { DatasetDetailLayout } from '@/components/data/dataset-detail/DatasetDetailLayout';
import { dataPath } from '@/config/client';
import { featureFlags } from '@/config/feature-flags';
import { fetchDatasetDetail } from '@/lib/dataset-detail-fetch';
import { datasetDetailPath, datasetListPath } from '@/lib/dataset-paths';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';
import { isNumericId } from '@/lib/utils/numeric-id';
import { truncateChars } from '@/lib/utils/truncate-chars';

interface DatasetDetailPageProps {
  params: Promise<{ id: string }>;
}

const PAGE_TITLE = 'Data set details';

/**
 * Resolves to null only when Django says 404 (unknown, not live/inactive,
 * inactive publisher, or not a timetable); any other failure throws.
 * Memoised per request so the page and `generateMetadata` share one call.
 */
const getDataset = cache((id: string) => fetchDatasetDetail<TimetableDatasetDetail>('timetables', id));

export default async function DatasetDetailPage({ params }: DatasetDetailPageProps) {
  // The feature flags are runtime (ECS) values, so render per request.
  await connection();

  const { id } = await params;

  // Django's route is <int:pk>, so a non-numeric id is a plain 404.
  if (!isNumericId(id)) {
    notFound();
  }

  const dataset = await getDataset(id);

  if (!dataset) {
    notFound();
  }

  return (
    <DatasetDetailLayout
      name={dataset.name}
      breadcrumbs={hostBreadcrumbs(
        'data',
        { label: 'Browse', href: dataPath('/search') },
        { label: 'Timetables Data', href: datasetListPath('TIMETABLE', { status: 'live' }) },
        { label: truncateChars(dataset.name, 19), href: datasetDetailPath('TIMETABLE', dataset.id) },
      )}
    >
      <TimetableDatasetDetailContent dataset={dataset} isSpecificFeedback={featureFlags.isSpecificFeedback} />
    </DatasetDetailLayout>
  );
}

export async function generateMetadata({ params }: DatasetDetailPageProps) {
  const { id } = await params;

  try {
    const dataset = isNumericId(id) ? await getDataset(id) : null;
    if (!dataset) {
      return { title: 'Page not found - Bus Open Data Service' };
    }
  } catch {
    // The page itself reports the failure; keep the metadata render quiet.
  }

  return { title: PAGE_TITLE };
}
