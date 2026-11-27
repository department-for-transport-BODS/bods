import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AvlDeleteSuccessContent } from '../../_components/AvlDeleteSuccessContent';

export const metadata: Metadata = {
  title: 'Data feed deleted',
};

export default function AvlDeleteSuccessPage() {
  return (
    <ProtectedRoute>
      <AvlDeleteSuccessContent />
    </ProtectedRoute>
  );
}
