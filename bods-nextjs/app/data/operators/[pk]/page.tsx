import { OperatorDetailContent } from '@/components/data/operators/OperatorDetailContent';

export const metadata = {
  title: 'Operator details',
};

interface OperatorDetailPageProps {
  params: Promise<{ pk: string }>;
}

export default async function OperatorDetailPage({ params }: OperatorDetailPageProps) {
  const { pk } = await params;
  return <OperatorDetailContent operatorId={pk} />;
}
