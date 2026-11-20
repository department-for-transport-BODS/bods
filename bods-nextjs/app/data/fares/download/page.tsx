import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { FaresDownloadContent } from './_components/FaresDownloadContent';

export const metadata = {
  title: { absolute: 'All fares data' },
  description: 'Download all fares data published on the Bus Open Data Service.',
};

export default function FaresDownloadPage() {
  return (
    <ProtectedRoute>
      <FaresDownloadContent />
    </ProtectedRoute>
  );
}
