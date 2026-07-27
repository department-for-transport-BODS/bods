import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AVLUpdateCancelContent } from '../../_components/AVLUpdateCancelContent';

export const metadata: Metadata = {
  title: 'Update data feed',
};

export default function AVLUpdateCancelPage() {
  return (
    <ProtectedRoute>
      <AVLUpdateCancelContent />
    </ProtectedRoute>
  );
}