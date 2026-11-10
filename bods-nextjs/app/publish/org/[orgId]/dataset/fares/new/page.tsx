import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { FaresCreatePageContent } from './_components/FaresCreatePageContent';

export default function FaresCreatePage() {
  return (
    <ProtectedRoute>
      <FaresCreatePageContent />
    </ProtectedRoute>
  );
}
