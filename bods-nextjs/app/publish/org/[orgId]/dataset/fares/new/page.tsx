import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { FaresCreatePageContent } from './_components/FaresCreatePageContent';

export const metadata = { title: 'Publish new data set: description' };

export default function FaresCreatePage() {
  return (
    <ProtectedRoute>
      <FaresCreatePageContent />
    </ProtectedRoute>
  );
}
