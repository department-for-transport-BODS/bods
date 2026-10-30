/**
 * AVL Dataset Detail Page
 *
 * Public URL: /avl/dataset/<pk>/ (Django "avl-feed-detail"). The page is
 * public, like Django's: anonymous users see everything except the API URL
 * panel, which needs their API key.
 *
 * Source: transit_odp/browse/templates/browse/avl/feed_detail/index.html
 * View: transit_odp/browse/views/avl_views.py - AVLDatasetDetailView
 * API: transit_odp/avl/views/dataset_detail_api.py - get_browse_avl_detail_api
 *
 * Server Component: the dataset is fetched on the server with the visitor's
 * session cookie, so an unknown / hidden / wrong-type id is a real HTTP 404.
 */

import { cache } from 'react';
import { notFound } from 'next/navigation';
import { connection } from 'next/server';
import { AvlDatasetDetailContent } from '@/components/data/dataset-detail/AvlDatasetDetailContent';
import { DatasetDetailLayout } from '@/components/data/dataset-detail/DatasetDetailLayout';
import type { AvlDatasetDetail } from '@/components/data/dataset-detail/types';
import { dataPath } from '@/config/client';
import { fetchDatasetDetail } from '@/lib/dataset-detail-fetch';
import { datasetDetailPath, datasetListPath } from '@/lib/dataset-paths';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';
import { isNumericId } from '@/lib/utils/numeric-id';
import { truncateChars } from '@/lib/utils/truncate-chars';

interface AvlDatasetDetailPageProps {
  params: Promise<{ id: string }>;
}

const PAGE_TITLE = 'Data feed details';

/** null only for Django's 404 (unknown, unpublished, inactive publisher, not AVL). */
const getDataset = cache((id: string) => fetchDatasetDetail<AvlDatasetDetail>('avl', id));

export default async function AvlDatasetDetailPage({ params }: AvlDatasetDetailPageProps) {
  // The page is per-visitor (API key, subscription state), so render per request.
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
      paddedHeading
      breadcrumbs={hostBreadcrumbs(
        'data',
        { label: 'Browse', href: dataPath('/search') },
        {
          label: 'Location Data',
          href: datasetListPath('AVL', { status: 'live' }),
        },
        {
          label: truncateChars(dataset.name, 19),
          href: datasetDetailPath('AVL', dataset.id),
        },
      )}
    >
      <AvlDatasetDetailContent dataset={dataset} />
    </DatasetDetailLayout>
  );
}

export async function generateMetadata({ params }: AvlDatasetDetailPageProps) {
  const { id } = await params;

  try {
    const dataset = isNumericId(id) ? await getDataset(id) : null;
    if (!dataset) {
      return { title: 'Page not found - Bus Open Data Service' };
    }
  } catch {
    // The page itself reports the failure; keep the metadata render quiet.
  }

  return { title: { absolute: PAGE_TITLE } };
}
