import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { TimetableUpdateContent } from '../../../_components/TimetableUpdateContent';

export const metadata: Metadata = { title: 'Provide data: upload' };

export default function TimetableReviewUpdatePage() {
  return (
    <ProtectedRoute>
      <TimetableUpdateContent mode="publishModify" />
    </ProtectedRoute>
  );
}
