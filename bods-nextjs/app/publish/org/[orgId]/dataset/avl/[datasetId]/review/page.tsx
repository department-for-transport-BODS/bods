'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AvlReviewPageContent } from '../../_components/AvlReviewPageContent';

export default function AVLReviewPage() {
  return (
    <ProtectedRoute>
      <AvlReviewPageContent
        reviewStatusPath="/api/avl/review-status"
        publishPath="/api/avl/publish"
        isUpdate={false}
      />
    </ProtectedRoute>
  );
}
