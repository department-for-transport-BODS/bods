import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { EditDescriptionContent } from '@/components/publish/EditDescriptionContent';

export default function FaresDatasetEditPage() {
  return (
    <ProtectedRoute>
      <EditDescriptionContent datasetType="fares" mode="live" />
    </ProtectedRoute>
  );
}
