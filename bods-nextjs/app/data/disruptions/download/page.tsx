import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DisruptionsDownloadContent } from './_components/DisruptionsDownloadContent';

export const metadata = {
  title: { absolute: 'All disruption data' },
  description: 'Download all disruption data published on the Bus Open Data Service.',
};

export default function DisruptionsDownloadPage() {
  return (
    <ProtectedRoute>
      <DisruptionsDownloadContent />
    </ProtectedRoute>
  );
}
