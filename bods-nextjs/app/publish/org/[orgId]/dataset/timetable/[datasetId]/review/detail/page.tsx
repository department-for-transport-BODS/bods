import { connection } from 'next/server';
import { featureFlags } from '@/config/feature-flags';
import LineDetailPageContent from './LineDetailPageContent';

export default async function PublishLineDetailPage() {
  await connection();

  return <LineDetailPageContent isTimetableVisualiserActive={featureFlags.isTimetableVisualiserActive} />;
}
