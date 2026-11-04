import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AvlArchiveSuccessContent } from '../../_components/AvlArchiveSuccessContent';

export const metadata: Metadata = {
  title: 'Data feed deactivated',
};

export default function AvlArchiveSuccessPage() {
  return (
    <ProtectedRoute>
      <AvlArchiveSuccessContent />
    </ProtectedRoute>
  );
}
