import { LicenceLineDetailContent } from '@/components/data/operators/LicenceLineDetailContent';

export const metadata = {
  title: 'Operator Licence line details',
};

interface LicenceLineDetailPageProps {
  params: Promise<{ number: string }>;
}

export default async function LicenceLineDetailPage({ params }: LicenceLineDetailPageProps) {
  const { number } = await params;
  return <LicenceLineDetailContent licenceNumber={number} />;
}
