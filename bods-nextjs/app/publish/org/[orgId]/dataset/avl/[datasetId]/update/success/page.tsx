'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AvlSuccessPanel } from '../../../_components/AvlSuccessPanel';

export default function AVLUpdateSuccessPage() {
  return (
    <ProtectedRoute>
      <AvlSuccessPanel update={true} />
    </ProtectedRoute>
  );
}
