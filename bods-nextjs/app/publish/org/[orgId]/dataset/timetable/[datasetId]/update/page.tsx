'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { TimetableUpdateContent } from '../../_components/TimetableUpdateContent';

export default function TimetableUpdatePage() {
  return (
    <ProtectedRoute>
      <TimetableUpdateContent mode="update" />
    </ProtectedRoute>
  );
}
