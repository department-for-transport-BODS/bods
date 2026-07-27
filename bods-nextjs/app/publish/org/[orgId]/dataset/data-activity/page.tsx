import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DataActivityContent } from './_components/DataActivityContent';

export const metadata: Metadata = {
  title: 'Data activity',
};

export default function DataActivityPage() {
  return (
    <ProtectedRoute>
      <DataActivityContent />
    </ProtectedRoute>
  );
}
