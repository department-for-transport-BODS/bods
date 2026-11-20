import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { FaresUpdatePageContent } from '../../../../_components/FaresUpdatePageContent';

export const metadata: Metadata = { title: 'Update data set: upload' };

export default function FaresUpdateReviewUpdatePage() {
  return (
    <ProtectedRoute>
      <FaresUpdatePageContent mode="updateModify" />
    </ProtectedRoute>
  );
}
