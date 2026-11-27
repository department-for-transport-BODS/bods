import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ContactOperatorSuccessContent } from '@/components/data/operators/ContactOperatorSuccessContent';

export const metadata = {
  title: 'Feedback sent',
};

export default function ContactOperatorSuccessPage() {
  return (
    <ProtectedRoute>
      <ContactOperatorSuccessContent />
    </ProtectedRoute>
  );
}
