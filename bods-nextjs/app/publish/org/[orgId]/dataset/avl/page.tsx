import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AvlManagement } from './_components/AvlManagement';

export const metadata: Metadata = {
  title: 'Review my bus location data',
};

export default function AVLPage() {
  return (
    <ProtectedRoute>
      <AvlManagement />
    </ProtectedRoute>
  );
}
