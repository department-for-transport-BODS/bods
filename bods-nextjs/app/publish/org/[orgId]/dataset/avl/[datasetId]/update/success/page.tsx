import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AvlSuccessPanel } from '../../../_components/AvlSuccessPanel';

export const metadata: Metadata = {
  title: 'Data feed updated',
};

export default function AVLUpdateSuccessPage() {
  return (
    <ProtectedRoute>
      <AvlSuccessPanel update />
    </ProtectedRoute>
  );
}
