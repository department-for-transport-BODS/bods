import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { TimetableFeedDetailContent } from './_components/TimetableFeedDetailContent';

export const metadata = {
  title: 'Data set details',
};

export default function TimetableFeedDetailPage() {
  return (
    <ProtectedRoute>
      <TimetableFeedDetailContent />
    </ProtectedRoute>
  );
}
