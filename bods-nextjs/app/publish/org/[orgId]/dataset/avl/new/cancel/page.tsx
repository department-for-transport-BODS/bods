import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AVLCreateCancelContent } from '../../_components/AVLCreateCancelContent';

export const metadata: Metadata = {
  title: 'Publish new data feed',
};

export default function AVLCreateCancelPage() {
  return (
    <ProtectedRoute>
      <AVLCreateCancelContent />
    </ProtectedRoute>
  );
}
