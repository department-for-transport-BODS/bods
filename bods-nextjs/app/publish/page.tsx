import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { PublishHomeContent } from './_components/PublishHomeContent';

export const metadata: Metadata = {
  title: 'Publish bus open data',
};

export default function PublishPage() {
  return (
    <ProtectedRoute>
      <PublishHomeContent />
    </ProtectedRoute>
  );
}
