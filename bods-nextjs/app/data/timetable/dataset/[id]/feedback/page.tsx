import { FeedbackPageContent } from '@/components/data/dataset-subpages/FeedbackPageContent';

export const metadata = { title: 'Provide feedback' };

export default function TimetableFeedbackPage() {
  return <FeedbackPageContent kind="timetables" />;
}
