import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { TimetableUpdateCancelContent } from '../../../_components/TimetableUpdateCancelContent';

export default function TimetableUpdateCancelPage() {
  return (
    <ProtectedRoute>
      <TimetableUpdateCancelContent />
    </ProtectedRoute>
  );
}