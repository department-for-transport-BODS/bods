import { AlertsBrowserPage } from '@/components/data/browser';

export default function DisruptionsPage() {
  return (
    <AlertsBrowserPage
      title="Disruption data"
      breadcrumbLabel="Disruption Data"
      description="Search for a specific Local Transport Authority"
      placeholder="Enter Local Transport Authority name"
      endpointPath="/api/v1/siri-sx/"
    />
  );
}

export const metadata = {
  title: 'Browse Disruption Data - Bus Open Data Service',
  description: 'Search and browse disruption data.',
};

