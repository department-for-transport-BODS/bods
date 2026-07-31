import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AvlArchivePageContent } from '../_components/AvlArchivePageContent';

export const metadata: Metadata = {
  title: 'Deactivate data feed',
};

export default function AvlArchivePage() {
  return (
    <ProtectedRoute>
      <AvlArchivePageContent />
    </ProtectedRoute>
  );
}
