import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { TimetableUpdateSuccessContent } from '../../../_components/TimetableUpdateSuccessContent';

export const metadata: Metadata = { title: 'Data set updated' };

export default function TimetableUpdateSuccessPage() {
  return (
    <ProtectedRoute>
      <TimetableUpdateSuccessContent update />
    </ProtectedRoute>
  );
}
