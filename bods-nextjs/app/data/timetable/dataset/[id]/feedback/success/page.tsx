import { FeedbackSuccessPageContent } from '@/components/data/dataset-subpages/FeedbackPageContent';

export const metadata = { title: 'Feedback sent' };

export default function TimetableFeedbackSuccessPage() {
  return <FeedbackSuccessPageContent kind="timetables" />;
}
