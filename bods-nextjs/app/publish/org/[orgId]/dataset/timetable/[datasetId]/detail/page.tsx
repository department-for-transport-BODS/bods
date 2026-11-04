import { connection } from 'next/server';
import { featureFlags } from '@/config/feature-flags';
import LineDetailPageContent from '../review/detail/LineDetailPageContent';

export default async function PublishedLineDetailPage() {
  await connection();

  return <LineDetailPageContent isTimetableVisualiserActive={featureFlags.isTimetableVisualiserActive} published />;
}
