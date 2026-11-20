import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { FaresUpdatePageContent } from '../../../_components/FaresUpdatePageContent';

export const metadata: Metadata = { title: 'Provide data: upload' };

export default function FaresReviewUpdatePage() {
  return (
    <ProtectedRoute>
      <FaresUpdatePageContent mode="publishModify" />
    </ProtectedRoute>
  );
}
