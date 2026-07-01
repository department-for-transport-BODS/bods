'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AvlFeedDetailContent } from './_components/AvlFeedDetailContent';

export default function AvlFeedDetailPage() {
  return (
    <ProtectedRoute>
      <AvlFeedDetailContent />
    </ProtectedRoute>
  );
}
