import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { FaresPublishSuccessPanel } from '../../_components/FaresPublishSuccessPanel';

export const metadata: Metadata = { title: 'Data set published' };

export default function FaresPublishSuccessPage() {
  return (
    <ProtectedRoute>
      <FaresPublishSuccessPanel />
    </ProtectedRoute>
  );
}
