import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AvlDownloadContent } from './_components/AvlDownloadContent';

export const metadata = {
  title: { absolute: 'All location data' },
  description: 'Download all bus location data published on the Bus Open Data Service.',
};

export default function AvlDownloadPage() {
  return (
    <ProtectedRoute>
      <AvlDownloadContent />
    </ProtectedRoute>
  );
}
