import { SubscriptionSuccessPageContent } from '@/components/data/dataset-subpages/SubscriptionPageContent';

export const metadata = { title: 'Subscribed successfully' };

export default function TimetableSubscriptionSuccessPage() {
  return <SubscriptionSuccessPageContent kind="timetables" />;
}
