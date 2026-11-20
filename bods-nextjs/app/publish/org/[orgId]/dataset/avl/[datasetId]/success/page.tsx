import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AvlSuccessPanel } from '../../_components/AvlSuccessPanel';

export const metadata: Metadata = {
  title: 'Data feed published',
};

export default function AVLPublishSuccessPage() {
  return (
    <ProtectedRoute>
      <AvlSuccessPanel update={false} />
    </ProtectedRoute>
  );
}
