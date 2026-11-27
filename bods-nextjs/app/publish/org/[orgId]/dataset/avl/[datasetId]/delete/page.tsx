import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AvlDeletePageContent } from '../_components/AvlDeletePageContent';

export const metadata: Metadata = {
  title: 'Delete data feed',
};

export default function AvlDeletePage() {
  return (
    <ProtectedRoute>
      <AvlDeletePageContent />
    </ProtectedRoute>
  );
}
