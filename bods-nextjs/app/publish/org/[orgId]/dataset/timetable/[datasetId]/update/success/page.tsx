'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { TimetableUpdateSuccessContent } from '../../../_components/TimetableUpdateSuccessContent';

export default function TimetableUpdateSuccessPage() {
  return (
    <ProtectedRoute>
      <TimetableUpdateSuccessContent />
    </ProtectedRoute>
  );
}
