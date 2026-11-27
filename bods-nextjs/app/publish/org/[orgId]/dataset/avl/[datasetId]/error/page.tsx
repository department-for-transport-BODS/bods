import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AVLErrorContent } from '../_components/AVLErrorContent';

export const metadata: Metadata = {
  title: 'Could not publish changes',
};

export default function AVLErrorPage() {
  return (
    <ProtectedRoute>
      <AVLErrorContent />
    </ProtectedRoute>
  );
}
