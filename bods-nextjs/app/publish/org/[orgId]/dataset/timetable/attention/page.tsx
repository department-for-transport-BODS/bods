import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { RequiresAttentionContent } from '@/components/publish/requires-attention/RequiresAttentionContent';

export const metadata: Metadata = {
  title: 'Service Codes Requiring Attention',
};

export default function TimetableAttentionPage() {
  return (
    <ProtectedRoute>
      <RequiresAttentionContent kind="timetables" />
    </ProtectedRoute>
  );
}
