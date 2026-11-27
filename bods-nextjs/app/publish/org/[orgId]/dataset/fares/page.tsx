import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ReviewListPage } from '@/components/publish/review-list/ReviewListPage';

export const metadata: Metadata = {
  title: 'Review my fares data',
};

export default function FaresReviewPage() {
  return (
    <ProtectedRoute>
      <ReviewListPage kind="fares" />
    </ProtectedRoute>
  );
}
