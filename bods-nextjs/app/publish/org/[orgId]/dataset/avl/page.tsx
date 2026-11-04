import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ReviewListPage } from '@/components/publish/review-list/ReviewListPage';

export const metadata: Metadata = {
  title: 'Review my bus location data',
};

export default function AVLPage() {
  return (
    <ProtectedRoute>
      <ReviewListPage kind="avl" />
    </ProtectedRoute>
  );
}
