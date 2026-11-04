import { LicenceDetailContent } from '@/components/data/operators/LicenceDetailContent';

export const metadata = {
  title: 'Operator Licence details',
};

interface LicenceDetailPageProps {
  params: Promise<{ number: string }>;
}

export default async function LicenceDetailPage({ params }: LicenceDetailPageProps) {
  const { number } = await params;
  return <LicenceDetailContent licenceNumber={number} />;
}
