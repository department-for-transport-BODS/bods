import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AvlFeedDetailContent } from './_components/AvlFeedDetailContent';

export const metadata = {
  title: 'Data feed details',
};

export default function AvlFeedDetailPage() {
  return (
    <ProtectedRoute>
      <AvlFeedDetailContent />
    </ProtectedRoute>
  );
}
