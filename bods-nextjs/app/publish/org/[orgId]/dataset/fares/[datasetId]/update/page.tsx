'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { FaresUpdatePageContent } from '../../_components/FaresUpdatePageContent';

export default function FaresUpdatePage() {
  return (
    <ProtectedRoute>
      <FaresUpdatePageContent mode="update" />
    </ProtectedRoute>
  );
}
