'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { PublishChangelogPageContent } from '@/components/publish/changelog/PublishChangelogPageContent';

export default function FaresChangelogPage() {
  return (
    <ProtectedRoute>
      <PublishChangelogPageContent kind="fares" />
    </ProtectedRoute>
  );
}
