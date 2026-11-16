import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { FaresUpdatePageContent } from '../../_components/FaresUpdatePageContent';

export const metadata: Metadata = { title: 'Update data set: comment' };

export default function FaresUpdatePage() {
  return (
    <ProtectedRoute>
      <FaresUpdatePageContent mode="update" />
    </ProtectedRoute>
  );
}
