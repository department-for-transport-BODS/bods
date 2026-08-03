import { connection } from 'next/server';
import { config } from '@/runtime-config';
import FaresReviewPageContent from './FaresReviewPageContent';

export default async function FaresReviewPage() {
  await connection();

  return <FaresReviewPageContent mapboxToken={config.mapboxToken} />;
}
