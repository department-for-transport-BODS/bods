'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { TimetableUpdateSuccessContent } from '../../_components/TimetableUpdateSuccessContent';

export default function TimetablePublishSuccessPage() {
  return (
    <ProtectedRoute>
      <TimetableUpdateSuccessContent />
    </ProtectedRoute>
  );
}
