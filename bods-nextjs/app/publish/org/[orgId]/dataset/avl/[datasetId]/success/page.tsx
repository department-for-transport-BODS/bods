'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AvlSuccessPanel } from '../../_components/AvlSuccessPanel';

export default function AVLPublishSuccessPage() {
  return (
    <ProtectedRoute>
      <AvlSuccessPanel update={false} />
    </ProtectedRoute>
  );
}
