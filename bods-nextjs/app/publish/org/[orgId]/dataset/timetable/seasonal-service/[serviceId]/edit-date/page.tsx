import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { SeasonalServiceEditDateContent } from '../../_components/SeasonalServiceEditDateContent';

export default function SeasonalServiceEditDatePage() {
  return (
    <ProtectedRoute>
      <SeasonalServiceEditDateContent />
    </ProtectedRoute>
  );
}
