import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AvlReviewPageContent } from '../../_components/AvlReviewPageContent';

export const metadata = {
  title: 'Publish new data feed: Review and publish',
};

export default function AVLReviewPage() {
  return (
    <ProtectedRoute>
      <AvlReviewPageContent isUpdate={false} />
    </ProtectedRoute>
  );
}
