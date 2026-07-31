import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AVLUpdatePageContent } from '../_components/AVLUpdatePageContent';

export const metadata: Metadata = {
  title: 'Update data feed',
};

export default function AVLUpdatePage() {
  return (
    <ProtectedRoute>
      <AVLUpdatePageContent />
    </ProtectedRoute>
  );
}
