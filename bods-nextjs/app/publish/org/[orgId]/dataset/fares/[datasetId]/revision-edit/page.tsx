import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { EditDescriptionContent } from '@/components/publish/EditDescriptionContent';

export default function FaresRevisionEditPage() {
  return (
    <ProtectedRoute>
      <EditDescriptionContent datasetType="fares" mode="draft" />
    </ProtectedRoute>
  );
}
