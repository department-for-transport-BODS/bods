import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { FaresPublishSuccessPanel } from '../../../_components/FaresPublishSuccessPanel';

export const metadata: Metadata = { title: 'Data set updated' };

export default function FaresUpdateSuccessPage() {
  return (
    <ProtectedRoute>
      <FaresPublishSuccessPanel update />
    </ProtectedRoute>
  );
}
