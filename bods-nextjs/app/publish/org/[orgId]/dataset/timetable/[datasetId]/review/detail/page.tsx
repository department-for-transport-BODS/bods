import { connection } from 'next/server';
import { featureFlags } from '@/config/feature-flags';
import LineDetailPageContent from './LineDetailPageContent';

// Django's title is the (data-dependent) line name, set client-side. Reset the
// "Review and publish" title inherited from the review layout.
export const metadata = { title: 'Bus Open Data Service' };

export default async function PublishLineDetailPage() {
  await connection();

  return <LineDetailPageContent isTimetableVisualiserActive={featureFlags.isTimetableVisualiserActive} />;
}
