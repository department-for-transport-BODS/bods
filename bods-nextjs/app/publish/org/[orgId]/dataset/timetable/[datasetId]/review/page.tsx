'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { TimetableReviewPageContent } from '../../_components/TimetableReviewPageContent';

export default function TimetableReviewPage() {
  return (
    <ProtectedRoute>
      <TimetableReviewPageContent />
    </ProtectedRoute>
  );
}
