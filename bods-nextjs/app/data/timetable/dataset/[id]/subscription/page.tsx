import { SubscriptionPageContent } from '@/components/data/dataset-subpages/SubscriptionPageContent';

export const metadata = { title: 'Subscribe to data set' };

export default function TimetableSubscriptionPage() {
  return <SubscriptionPageContent kind="timetables" />;
}
