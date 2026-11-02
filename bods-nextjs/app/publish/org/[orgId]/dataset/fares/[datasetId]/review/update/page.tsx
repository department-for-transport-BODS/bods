'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { FaresUpdatePageContent } from '../../../_components/FaresUpdatePageContent';

export default function FaresReviewUpdatePage() {
  return (
    <ProtectedRoute>
      <FaresUpdatePageContent mode="publishModify" />
    </ProtectedRoute>
  );
}
