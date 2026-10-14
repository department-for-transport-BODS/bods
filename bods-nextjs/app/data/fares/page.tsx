import { DatasetBrowserPage } from '@/components/data/browser';
import { featureFlags } from '@/config/feature-flags';

export default function FaresPage() {
  return (
    <DatasetBrowserPage
      title="Fares data"
      breadcrumbLabel="Fares Data"
      description="Search for a specific operator or NOC"
      placeholder="Search by NOC or Operator"
      endpointPath="/api/browser/fares/"
      typeLabel="Fares data"
      idLabel="Data set ID:"
      lastUpdatedLabel="Last updated:"
      includeAreaFilter
      includeComplianceInResult={featureFlags.isFaresValidatorActive}
    />
  );
}

export const metadata = {
  title: 'Browse Fares Data - Bus Open Data Service',
  description: 'Search and browse fares datasets.',
};

