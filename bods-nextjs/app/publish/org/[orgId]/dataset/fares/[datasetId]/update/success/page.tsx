'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { FaresPublishSuccessPanel } from '../../../_components/FaresPublishSuccessPanel';

export default function FaresUpdateSuccessPage() {
  return (
    <ProtectedRoute>
      <FaresPublishSuccessPanel update />
    </ProtectedRoute>
  );
}
