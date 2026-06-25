'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AvlReviewPageContent } from '../../../_components/AvlReviewPageContent';

export default function AVLUpdateReviewPage() {
  return (
    <ProtectedRoute>
      <AvlReviewPageContent isUpdate />
    </ProtectedRoute>
  );
}
