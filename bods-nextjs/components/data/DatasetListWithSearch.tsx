'use client';

/**
 * Dataset List with Search and Filters Component
 *
 *
 * Wrapper component that combines DatasetSearch, DatasetFilters, and DatasetList.
 * Handles URL-based search and filter state.
 *
 *
 */

import { useSearchParams } from 'next/navigation';
import { DatasetSearch } from './DatasetSearch';
import { DatasetFilters } from './DatasetFilters';
import { ActiveFilterTags } from './ActiveFilterTags';
import { DatasetList } from './DatasetList';
import { useFilterOptions } from '@/hooks/useFilterOptions';
import type { DatasetListItem, PaginatedResponse } from '@/types';

interface DatasetListWithSearchProps {
  /** Initial datasets to display (from server fetch) */
  initialData?: PaginatedResponse<DatasetListItem>;
  /** Number of results per page */
  pageSize?: number;
  /** Initial search query from URL (server-side) */
  initialSearch?: string;
  /** Initial filters from URL (server-side) */
  initialFilters?: {
    area?: string;
    organisation?: string;
    status?: string;
    dataType?: string;
  };
}

export function DatasetListWithSearch({
  initialData,
  pageSize = 20,
  initialSearch = '',
  initialFilters = {},
}: DatasetListWithSearchProps) {
  const searchParams = useSearchParams();

  const currentSearch = searchParams.get('search') || initialSearch;

  const currentFilters = {
    area: searchParams.get('area') || initialFilters.area || undefined,
    organisation: searchParams.get('organisation') || initialFilters.organisation || undefined,
    status: searchParams.get('status') || initialFilters.status || undefined,
    dataType: searchParams.get('dataType') || initialFilters.dataType || undefined,
  };

  const { areas, organisations, isLoading: isLoadingOptions } = useFilterOptions();

  return (
    <div className="dataset-list-with-search" data-testid="dataset-list-with-search">
      <div className="govuk-grid-row">
        <div className="govuk-grid-column-full">
          <DatasetSearch />
        </div>
      </div>

      <div className="govuk-grid-row govuk-!-margin-top-6">
        <div className="govuk-grid-column-one-third">
          <DatasetFilters
            areas={areas}
            organisations={organisations}
            isLoading={isLoadingOptions}
          />
        </div>

        <div className="govuk-grid-column-two-thirds">
          <ActiveFilterTags
            areas={areas}
            organisations={organisations}
          />

          <DatasetList
            initialData={
              currentSearch === initialSearch &&
              JSON.stringify(currentFilters) === JSON.stringify(initialFilters)
                ? initialData
                : undefined
            }
            pageSize={pageSize}
            searchQuery={currentSearch}
            filters={currentFilters}
          />
        </div>
      </div>
    </div>
  );
}

