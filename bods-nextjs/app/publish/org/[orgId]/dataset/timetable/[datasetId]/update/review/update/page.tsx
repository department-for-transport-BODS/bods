import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { TimetableUpdateContent } from '../../../../_components/TimetableUpdateContent';

export const metadata: Metadata = { title: 'Update data set: upload' };

export default function TimetableUpdateReviewUpdatePage() {
  return (
    <ProtectedRoute>
      <TimetableUpdateContent mode="updateModify" />
    </ProtectedRoute>
  );
}
