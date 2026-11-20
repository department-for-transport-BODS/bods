import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { EditDescriptionContent } from '@/components/publish/EditDescriptionContent';

export default function TimetableDatasetEditPage() {
  return (
    <ProtectedRoute>
      <EditDescriptionContent datasetType="timetable" mode="live" />
    </ProtectedRoute>
  );
}
