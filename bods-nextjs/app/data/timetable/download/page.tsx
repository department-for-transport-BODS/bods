import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { TimetableDownloadContent } from './_components/TimetableDownloadContent';

export const metadata = {
  title: { absolute: 'All timetables data' },
  description: 'Download all timetables data published on the Bus Open Data Service.',
};

export default function TimetableDownloadPage() {
  return (
    <ProtectedRoute>
      <TimetableDownloadContent />
    </ProtectedRoute>
  );
}
