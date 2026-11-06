import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { FaresCreatePageContent } from './_components/FaresCreatePageContent';

export const metadata: Metadata = {
  title: 'Publish new data set: description',
};

export default function FaresCreatePage() {
  return (
    <ProtectedRoute>
      <FaresCreatePageContent />
    </ProtectedRoute>
  );
}
