import { connection } from 'next/server';
import { serverConfig } from '@/config/server';
import FaresReviewPageContent from './FaresReviewPageContent';

export default async function FaresReviewPage() {
  await connection();

  return <FaresReviewPageContent mapboxToken={serverConfig.mapboxToken} />;
}
