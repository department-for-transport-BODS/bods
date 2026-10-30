import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ContactOperatorContent } from '@/components/data/operators/ContactOperatorContent';

export const metadata = {
  title: 'Provide feedback',
};

interface ContactOperatorPageProps {
  params: Promise<{ pk: string }>;
}

export default async function ContactOperatorPage({ params }: ContactOperatorPageProps) {
  const { pk } = await params;
  return (
    <ProtectedRoute>
      <ContactOperatorContent operatorId={pk} />
    </ProtectedRoute>
  );
}
