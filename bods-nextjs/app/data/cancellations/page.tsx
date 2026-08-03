import { AlertsBrowserPage } from '@/components/data/browser';

export default function CancellationsPage() {
  return (
    <AlertsBrowserPage
      title="Cancellation data"
      breadcrumbLabel="Cancellation Data"
      description="Search for cancellation data"
      placeholder="Search cancellations"
      endpointPath="/api/v1/siri-sx/cancellations/"
    />
  );
}

export const metadata = {
  title: 'Browse Cancellation Data - Bus Open Data Service',
  description: 'Search and browse cancellations data.',
};

