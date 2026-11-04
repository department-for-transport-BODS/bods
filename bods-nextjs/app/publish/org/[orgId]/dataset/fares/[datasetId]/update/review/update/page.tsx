'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { FaresUpdatePageContent } from '../../../../_components/FaresUpdatePageContent';

export default function FaresUpdateReviewUpdatePage() {
  return (
    <ProtectedRoute>
      <FaresUpdatePageContent mode="updateModify" />
    </ProtectedRoute>
  );
}
