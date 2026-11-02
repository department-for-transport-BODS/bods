import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { EditDescriptionContent } from '@/components/publish/EditDescriptionContent';

export default function TimetableRevisionEditPage() {
  return (
    <ProtectedRoute>
      <EditDescriptionContent datasetType="timetable" mode="draft" />
    </ProtectedRoute>
  );
}
