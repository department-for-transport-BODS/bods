import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { TimetableUpdateCancelContent } from '../../../_components/TimetableUpdateCancelContent';

export const metadata: Metadata = {
  title: 'Update data set: cancel',
};

export default function TimetableUpdateCancelPage() {
  return (
    <ProtectedRoute>
      <TimetableUpdateCancelContent />
    </ProtectedRoute>
  );
}