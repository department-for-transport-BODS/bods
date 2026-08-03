import { DatasetBrowserPage } from '@/components/data/browser';

export default function AvlPage() {
  return (
    <DatasetBrowserPage
      title="Location data"
      breadcrumbLabel="Location Data"
      description="Search for a specific operator or NOC"
      placeholder="Search by NOC or Operator"
      endpointPath="/api/v1/datafeed/"
      typeLabel="Bus location data"
      idLabel="Data feed ID:"
      lastUpdatedLabel="Last automated update:"
    />
  );
}

export const metadata = {
  title: 'Browse Location Data - Bus Open Data Service',
  description: 'Search and browse bus location data feeds.',
};

