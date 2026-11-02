'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { FaresPublishSuccessPanel } from '../../_components/FaresPublishSuccessPanel';

export default function FaresPublishSuccessPage() {
  return (
    <ProtectedRoute>
      <FaresPublishSuccessPanel />
    </ProtectedRoute>
  );
}
