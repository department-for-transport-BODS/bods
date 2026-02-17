import { DatasetBrowserPage } from '@/components/data/browser';

export default function FaresPage() {
  return (
    <DatasetBrowserPage
      title="Fares data"
      breadcrumbLabel="Fares Data"
      description="Search for a specific operator or NOC"
      placeholder="Search by NOC or Operator"
      endpointPath="/api/v1/fares/dataset/"
      typeLabel="Fares data"
      idLabel="Data set ID:"
      lastUpdatedLabel="Last updated:"
      includeAreaFilter
    />
  );
}

export const metadata = {
  title: 'Browse Fares Data - Bus Open Data Service',
  description: 'Search and browse fares datasets.',
};

