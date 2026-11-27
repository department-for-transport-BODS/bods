import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ReviewListPage } from '@/components/publish/review-list/ReviewListPage';

export const metadata: Metadata = {
  title: 'Review my timetables data',
};

export default function TimetableReviewPage() {
  return (
    <ProtectedRoute>
      <ReviewListPage kind="timetable" />
    </ProtectedRoute>
  );
}
