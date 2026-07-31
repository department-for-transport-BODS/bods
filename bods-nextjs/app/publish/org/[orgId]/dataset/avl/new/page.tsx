import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AVLCreatePageContent } from '../_components/AVLCreatePageContent';

export const metadata: Metadata = {
  title: 'Publish new data feed',
};

export default function AVLCreatePage() {
  return (
    <ProtectedRoute>
      <AVLCreatePageContent />
    </ProtectedRoute>
  );
}
