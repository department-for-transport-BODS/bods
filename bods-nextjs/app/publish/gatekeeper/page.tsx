import type { Metadata } from 'next';
import { PublishGatekeeperContent } from './_components/PublishGatekeeperContent';

export const metadata: Metadata = {
  title: 'Publish your data',
};

export default function PublishGatekeeperPage() {
  return <PublishGatekeeperContent />;
}
