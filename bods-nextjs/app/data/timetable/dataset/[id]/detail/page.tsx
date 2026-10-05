import { connection } from 'next/server';
import { featureFlags } from '@/config/feature-flags';
import LineDetailPageContent from './LineDetailPageContent';

export default async function DataLineDetailPage() {
  await connection();

  return (
    <LineDetailPageContent
      isTimetableVisualiserActive={featureFlags.isTimetableVisualiserActive}
      isSpecificFeedback={featureFlags.isSpecificFeedback}
    />
  );
}
