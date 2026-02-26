'use client';

/**
 * Dataset List Component
 *
 *
 * Client component that displays a list of datasets with:
 * - Paginated results using shared Pagination component
 * - Loading states
 * - Error handling
 * - URL-based pagination
 *
 */

import { useEffect, useState, useCallback, useMemo } from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { DatasetCard } from './DatasetCard';
import { Pagination } from '@/components/shared/Pagination';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { ErrorDisplay } from '@/components/shared/ErrorDisplay';
import type { DatasetListItem, PaginatedResponse } from '@/types';
import { config } from '@/config';

interface DatasetListProps {
  /** Initial datasets to display (from server fetch) */
  initialData?: PaginatedResponse<DatasetListItem>;
  /** API endpoint for fetching datasets */
  apiEndpoint?: string;
  /** Number of results per page */
  pageSize?: number;
  /** Search query from URL (passed from parent) */
  searchQuery?: string;
  /** Filter values for filtering datasets */
  filters?: {
    area?: string;
    organisation?: string;
    status?: string;
    dataType?: string;
  };
}

const DEFAULT_PAGE_SIZE = 20;
type DatasetFilters = NonNullable<DatasetListProps['filters']>;

export function DatasetList({
  initialData,
  apiEndpoint = '/api/v1/dataset/',
  pageSize = DEFAULT_PAGE_SIZE,
  searchQuery,
  filters,
}: DatasetListProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const rawPage = parseInt(searchParams.get('page') || '1', 10);
  const currentPage = Number.isNaN(rawPage) || rawPage < 1 ? 1 : rawPage;
  const currentSearch = searchQuery ?? searchParams.get('search') ?? '';

  const currentFilters = useMemo<DatasetFilters>(
    () =>
      filters || {
        area: searchParams.get('area') || undefined,
        organisation: searchParams.get('organisation') || undefined,
        status: searchParams.get('status') || undefined,
        dataType: searchParams.get('dataType') || undefined,
      },
    [filters, searchParams]
  );

  const [datasets, setDatasets] = useState<DatasetListItem[]>(initialData?.results ?? []);
  const [totalCount, setTotalCount] = useState<number>(initialData?.count ?? 0);
  const [isLoading, setIsLoading] = useState<boolean>(!initialData);
  const [error, setError] = useState<string | null>(null);

  const totalPages = Math.ceil(totalCount / pageSize);

  const fetchDatasets = useCallback(
    async (page: number, search = '', filterParams?: DatasetFilters) => {
      setIsLoading(true);
      setError(null);

      try {
        const offset = (page - 1) * pageSize;
        const apiUrl = config.djangoApiUrl;
        let url = `${apiUrl}${apiEndpoint}?limit=${pageSize}&offset=${offset}`;

        if (search.trim()) {
          url += `&search=${encodeURIComponent(search.trim())}`;
        }

        if (filterParams) {
          if (filterParams.area) {
            url += `&adminArea=${encodeURIComponent(filterParams.area)}`;
          }
          if (filterParams.organisation) {
            url += `&organisation=${encodeURIComponent(filterParams.organisation)}`;
          }
          if (filterParams.status) {
            url += `&status=${encodeURIComponent(filterParams.status)}`;
          }
          if (filterParams.dataType) {
            url += `&dataset_type=${encodeURIComponent(filterParams.dataType)}`;
          }
        }

        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        });

        if (!response.ok) {
          if (response.status === 401) {
            throw new Error('Authentication required to view datasets');
          }
          throw new Error(`Failed to load datasets: ${response.statusText}`);
        }

        const data: PaginatedResponse<Record<string, unknown>> = await response.json();
        const transformedResults: DatasetListItem[] = data.results.map((item) => ({
          id: item.id as number,
          name: item.name as string,
          operatorName:
            (item.operatorName as string | undefined) ||
            (item.operator_name as string | undefined) ||
            '',
          description: (item.description as string | undefined) || '',
          status: ((item.status as DatasetListItem['status']) || 'published') as DatasetListItem['status'],
          modified: (item.modified as string | undefined) || new Date().toISOString(),
          dqScore:
            (item.dqScore as string | undefined) ||
            (item.dq_score as string | undefined) ||
            '0%',
          dqRag:
            (item.dqRag as DatasetListItem['dqRag'] | undefined) ||
            (item.dq_rag as DatasetListItem['dqRag'] | undefined) ||
            'unavailable',
          dataType:
            (item.dataType as DatasetListItem['dataType'] | undefined) ||
            (item.dataset_type as DatasetListItem['dataType'] | undefined) ||
            'TIMETABLE',
        }));

        setDatasets(transformedResults);
        setTotalCount(data.count);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unexpected error occurred');
      } finally {
        setIsLoading(false);
      }
    },
    [apiEndpoint, pageSize]
  );

  useEffect(() => {
    const hasFilters = Object.values(currentFilters).some((value) => Boolean(value));

    if (initialData && currentPage === 1 && !currentSearch && !hasFilters) {
      setDatasets(initialData.results);
      setTotalCount(initialData.count);
      setError(null);
      setIsLoading(false);
      return;
    }

    fetchDatasets(currentPage, currentSearch, currentFilters);
  }, [currentPage, currentSearch, currentFilters, fetchDatasets, initialData]);

  const handlePageChange = (newPage: number) => {
    const params = new URLSearchParams(searchParams.toString());
    if (newPage === 1) {
      params.delete('page');
    } else {
      params.set('page', newPage.toString());
    }
    const queryString = params.toString();
    router.push(queryString ? `${pathname}?${queryString}` : pathname);
  };

  const handleRetry = () => {
    fetchDatasets(currentPage, currentSearch, currentFilters);
  };

  if (isLoading) {
    return (
      <LoadingSpinner
        message="Loading datasets..."
        size="large"
        centered
      />
    );
  }

  if (error) {
    return (
      <ErrorDisplay
        type={error.includes('Authentication') ? 'forbidden' : 'server'}
        message={error}
        onRetry={handleRetry}
        showContactLink
      />
    );
  }

  if (datasets.length === 0) {
    return (
      <div className="dataset-list-empty" role="status" data-testid="dataset-list-empty">
        <p className="govuk-body-l">No datasets found{currentSearch ? ` for "${currentSearch}"` : ''}.</p>
        <p className="govuk-body">
          {currentSearch
            ? 'Try different keywords or clear the search to view all datasets.'
            : 'Try adjusting your filter criteria.'}
        </p>
      </div>
    );
  }

  return (
    <div className="dataset-list" data-testid="dataset-list">
      <div className="govuk-body govuk-!-margin-bottom-4" aria-live="polite">
        <span className="govuk-visually-hidden">Search results: </span>
        {totalCount.toLocaleString()} dataset{totalCount !== 1 ? 's' : ''} found
        {currentSearch && <span> for &quot;{currentSearch}&quot;</span>}
      </div>

      <div
        className="dataset-list__items"
        role="list"
        aria-label="Dataset results"
      >
        {datasets.map((dataset) => (
          <div key={dataset.id} role="listitem">
            <DatasetCard dataset={dataset} />
          </div>
        ))}
      </div>

      {totalPages > 1 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          totalResults={totalCount}
          resultsPerPage={pageSize}
          onPageChange={handlePageChange}
          pageParam="page"
        />
      )}

      <style jsx>{`
        .dataset-list {
          margin-top: 20px;
        }

        .dataset-list__items {
          margin-bottom: 30px;
        }

        .dataset-list-empty {
          text-align: center;
          padding: 40px 20px;
          background-color: #f3f2f1;
          border-radius: 4px;
        }
      `}</style>
    </div>
  );
}

