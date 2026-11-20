import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AvlReviewPageContent } from '../../../_components/AvlReviewPageContent';

export const metadata = { title: 'Review and publish' };

export default function AVLUpdateReviewPage() {
  return (
    <ProtectedRoute>
      <AvlReviewPageContent isUpdate />
    </ProtectedRoute>
  );
}
