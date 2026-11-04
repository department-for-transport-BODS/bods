import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { SeasonalServiceAddNewContent } from '../_components/SeasonalServiceAddNewContent';

export default function SeasonalServiceAddNewPage() {
  return (
    <ProtectedRoute>
      <SeasonalServiceAddNewContent />
    </ProtectedRoute>
  );
}
