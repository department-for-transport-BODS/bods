/**
 * Data Browse Page - Server Component
 * 
 * 
 * Main page for browsing datasets (data subdomain).
 * Server Component for optimal performance and SEO.
 * Fetches initial data server-side and passes to client component.
 */

import { Suspense } from 'react';
import { DatasetListWithSearch } from '@/components/data/DatasetListWithSearch';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import type { DatasetListItem, PaginatedResponse } from '@/types';

const PAGE_SIZE = 20;

interface SearchParams {
  search?: string;
  page?: string;
  area?: string;
  organisation?: string;
  status?: string;
  dataType?: string;
}

/**
 * Fetch datasets from Django API (server-side)
 */
async function getDatasets(
  search?: string,
  filters?: {
    area?: string;
    organisation?: string;
    status?: string;
    dataType?: string;
  }
): Promise<PaginatedResponse<DatasetListItem> | null> {
  try {
    const apiUrl = process.env.DJANGO_API_URL || process.env.NEXT_PUBLIC_DJANGO_API_URL || 'http://localhost:8000';
    let url = `${apiUrl}/api/v1/dataset/?limit=${PAGE_SIZE}&offset=0`;
    
    if (search?.trim()) {
      url += `&search=${encodeURIComponent(search.trim())}`;
    }
    
    if (filters) {
      if (filters.area) {
        url += `&adminArea=${encodeURIComponent(filters.area)}`;
      }
      if (filters.organisation) {
        url += `&organisation=${encodeURIComponent(filters.organisation)}`;
      }
      if (filters.status) {
        url += `&status=${encodeURIComponent(filters.status)}`;
      }
      if (filters.dataType) {
        url += `&dataset_type=${encodeURIComponent(filters.dataType)}`;
      }
    }
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      next: { revalidate: 300 },
    });

    if (!response.ok) {
      console.error(`Failed to fetch datasets: ${response.status} ${response.statusText}`);
      return null;
    }

    const data = await response.json();
    
    const transformedResults: DatasetListItem[] = data.results.map((item: Record<string, unknown>) => ({
      id: item.id as number,
      name: item.name as string,
      operatorName: item.operatorName as string,
      description: (item.description as string) || '',
      status: (item.status as DatasetListItem['status']) || 'published',
      modified: item.modified as string,
      dqScore: (item.dqScore as string) || '0%',
  const filters = {
    area: params.area,
    organisation: params.organisation,
    status: params.status,
    dataType: params.dataType,
  };
  
  const initialData = await getDatasets(searchQuery, filters

    return {
      count: data.count,
      next: data.next,
      previous: data.previous,
      results: transformedResults,
    };
  } catch (error) {
    console.error('Error fetching datasets:', error);
    return null;
  }
}

interface DataBrowsePageProps {
  searchParams: Promise<SearchParams>;
}

export default async function DataBrowsePage({ searchParams }: DataBrowsePageProps) {
  const params = await searchParams;
  const searchQuery = params.search || '';
  
  const initialData = await getDatasets(searchQuery);

  return (
    <div className="govuk-width-container">
      <main className="govuk-main-wrapper" id="main-content" role="main">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-full">
            <h1 className="govuk-heading-xl">Browse bus data</h1>
            <p className="govuk-body-l">
              Find and download bus timetable, location, and fares data from operators across England.
            </p>

            <div className="govuk-!-margin-bottom-6">
              <h2 className="govuk-heading-m">Browse by data type</h2>
              <ul className="govuk-list govuk-list--bullet">
                <li>
                  <a href="/data/timetables" className="govuk-link">
                    Timetables
                  </a>
                  {' - '}TransXChange schedule data
                </li>
                <li>
                  <a href="/data/avl" className="govuk-link">
                    Bus location data (AVL)
                  </a>
                  {' - '}Real-time vehicle positions
                </li>
                <li>
                  <a href="/data/fares" className="govuk-link">
                    Fares data
                  </a>
                  {' - '}NeTEx pricing information
                </li>
              </ul>
            </div>

            <section aria-labelledby="datasets-heading">
              <h2 id="datasets-heading" className="govuk-heading-l">
                All datasets
              </h2>
              
              <Suspense fallback={
                <LoadingSpinner 
                  message="Loading datasets..." 
                  size="large" 
                  centered 
                  initialFilters={filters}
                />
              }>
                <DatasetListWithSearch 
                  initialData={initialData || undefined}
                  pageSize={PAGE_SIZE}
                  initialSearch={searchQuery}
                />
              </Suspense>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}

/**
 * Metadata for the page
 */
export const metadata = {
  title: 'Browse Bus Data - Bus Open Data Service',
  description: 'Browse and download bus timetable, location, and fares data from operators across England.',
};
