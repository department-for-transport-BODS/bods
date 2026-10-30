/**
 * Fares Dataset Detail Page
 *
 * Public URL: /fares/dataset/<pk>/ (Django "fares-feed-detail"). The page is
 * public, like Django's: anonymous users see everything except the API URL
 * panel, which needs their API key.
 *
 * Source: transit_odp/browse/templates/browse/fares/feed_detail/index.html
 * View: transit_odp/browse/views/fares_views.py - FaresDatasetDetailView
 * API: transit_odp/fares/views/dataset_detail_api.py - get_browse_fares_detail_api
 *
 * Server Component: the dataset is fetched on the server with the visitor's
 * session cookie, so an unknown / hidden / wrong-type id is a real HTTP 404.
 */

import { cache } from 'react';
import { notFound } from 'next/navigation';
import { connection } from 'next/server';
import { DatasetDetailLayout } from '@/components/data/dataset-detail/DatasetDetailLayout';
import { FaresDatasetDetailContent } from '@/components/data/dataset-detail/FaresDatasetDetailContent';
import type { FaresDatasetDetail } from '@/components/data/dataset-detail/types';
import { dataPath } from '@/config/client';
import { featureFlags } from '@/config/feature-flags';
import { fetchDatasetDetail } from '@/lib/dataset-detail-fetch';
import { datasetDetailPath, datasetListPath } from '@/lib/dataset-paths';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';
import { isNumericId } from '@/lib/utils/numeric-id';
import { truncateChars } from '@/lib/utils/truncate-chars';

interface FaresDatasetDetailPageProps {
  params: Promise<{ id: string }>;
}

const PAGE_TITLE = 'Data set details';

/** null only for Django's 404 (unknown, unpublished, inactive publisher, not fares). */
const getDataset = cache((id: string) => fetchDatasetDetail<FaresDatasetDetail>('fares', id));

export default async function FaresDatasetDetailPage({ params }: FaresDatasetDetailPageProps) {
  // The feature flags are runtime (ECS) values and the page is per-visitor, so render per request.
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
          label: 'Fares Data',
          href: datasetListPath('FARES', { status: 'live' }),
        },
        {
          label: truncateChars(dataset.name, 19),
          href: datasetDetailPath('FARES', dataset.id),
        },
      )}
    >
      <FaresDatasetDetailContent
        dataset={dataset}
        isFaresValidatorActive={featureFlags.isFaresValidatorActive}
      />
    </DatasetDetailLayout>
  );
}

export async function generateMetadata({ params }: FaresDatasetDetailPageProps) {
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
