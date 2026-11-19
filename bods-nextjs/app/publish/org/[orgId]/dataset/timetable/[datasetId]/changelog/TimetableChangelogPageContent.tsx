'use client';

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { PublishChangelogPageContent } from '@/components/publish/changelog/PublishChangelogPageContent';

export default function TimetableChangelogPage() {
  return (
    <ProtectedRoute>
      <PublishChangelogPageContent kind="timetables" />
    </ProtectedRoute>
  );
}
