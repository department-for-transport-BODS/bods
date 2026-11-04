import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { SeasonalServicesListContent } from './_components/SeasonalServicesListContent';

export const metadata: Metadata = {
  title: 'Manage seasonal services',
};

export default function SeasonalServicesPage() {
  return (
    <ProtectedRoute>
      <SeasonalServicesListContent />
    </ProtectedRoute>
  );
}
