import { DatasetBrowserPage } from '@/components/data/browser';

export default function TimetablesPage() {
  return (
    <DatasetBrowserPage
        title="Timetables data"
        breadcrumbLabel="Timetables Data"
        description="Search for a specific operator or NOC"
        placeholder="Search by NOC or Operator"
        endpointPath="/api/v1/dataset/"
        typeLabel="Timetables data"
        idLabel="Data set ID:"
        lastUpdatedLabel="Last updated:"
        includeAreaFilter
        includeDateFilters
        includeStartDateInResult
      />
  );
}

