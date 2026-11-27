import { SubscriptionPageContent } from '@/components/data/dataset-subpages/SubscriptionPageContent';

export const metadata = { title: 'Subscribe to data feed' };

export default function AvlSubscriptionPage() {
  return <SubscriptionPageContent kind="avl" />;
}
