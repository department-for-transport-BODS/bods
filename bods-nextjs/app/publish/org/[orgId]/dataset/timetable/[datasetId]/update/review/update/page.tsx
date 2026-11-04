'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { TimetableUpdateContent } from '../../../../_components/TimetableUpdateContent';

export default function TimetableUpdateReviewUpdatePage() {
  return (
    <ProtectedRoute>
      <TimetableUpdateContent mode="updateModify" />
    </ProtectedRoute>
  );
}
