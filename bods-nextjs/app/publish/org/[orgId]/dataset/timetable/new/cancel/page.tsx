import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { TimetableCreateCancelContent } from '../../_components/TimetableCreateCancelContent';

export const metadata: Metadata = {
  title: 'Publish new data set',
};

export default function TimetableCreateCancelPage() {
  return (
    <ProtectedRoute>
      <TimetableCreateCancelContent />
    </ProtectedRoute>
  );
}