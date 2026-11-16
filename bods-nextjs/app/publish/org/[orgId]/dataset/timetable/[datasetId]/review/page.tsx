import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { TimetableReviewPageContent } from '../../_components/TimetableReviewPageContent';

export const metadata: Metadata = { title: 'Review and publish' };

export default function TimetableReviewPage() {
  return (
    <ProtectedRoute>
      <TimetableReviewPageContent />
    </ProtectedRoute>
  );
}
