import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { TimetableUpdateSuccessContent } from '../../_components/TimetableUpdateSuccessContent';

export const metadata: Metadata = { title: 'Data set published' };

export default function TimetablePublishSuccessPage() {
  return (
    <ProtectedRoute>
      <TimetableUpdateSuccessContent />
    </ProtectedRoute>
  );
}
