import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { TimetableUpdateContent } from '../../_components/TimetableUpdateContent';

export const metadata: Metadata = { title: 'Update data set: comment' };

export default function TimetableUpdatePage() {
  return (
    <ProtectedRoute>
      <TimetableUpdateContent mode="update" />
    </ProtectedRoute>
  );
}
