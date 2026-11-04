import { connection } from 'next/server';
import { serverConfig } from '@/config/server';
import FaresReviewPageContent from '../../review/FaresReviewPageContent';

export default async function FaresUpdateReviewPage() {
  await connection();

  return <FaresReviewPageContent mapboxToken={serverConfig.mapboxToken} isUpdate />;
}
