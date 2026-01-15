/**
 * Filter Options Hook
 * 
 * 
 * Fetches available filter options from Django API:
 * - AdminArea (regions)
 * - Organisation (operators)
 */

import { useState, useEffect } from 'react';
import type { FilterOption } from '@/components/data/DatasetFilters';

interface FilterOptionsData {
  areas: FilterOption[];
  organisations: FilterOption[];
  isLoading: boolean;
  error: string | null;
}

/**
 * Fetch filter options from the API
 * 
 * Uses Django REST Framework endpoints:
 * - /api/v1/admin-area/ for regions
 * - /api/v1/organisation/ for operators
 */
export function useFilterOptions(): FilterOptionsData {
  const [areas, setAreas] = useState<FilterOption[]>([]);
  const [organisations, setOrganisations] = useState<FilterOption[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOptions = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const apiUrl = process.env.NEXT_PUBLIC_DJANGO_API_URL || 'http://localhost:8000';

        const [areasResponse, orgsResponse] = await Promise.all([
          fetch(`${apiUrl}/api/v1/admin-area/`, {
            headers: {
              'Content-Type': 'application/json',
            },
          }),
          fetch(`${apiUrl}/api/v1/organisation/?is_active=true`, {
            headers: {
              'Content-Type': 'application/json',
            },
          }),
        ]);

        if (!areasResponse.ok || !orgsResponse.ok) {
          throw new Error('Failed to fetch filter options');
        }

        const [areasData, orgsData] = await Promise.all([
          areasResponse.json(),
          orgsResponse.json(),
        ]);

        const areaOptions: FilterOption[] = (areasData.results || [])
          .map((area: { id: number; name: string; atco_code?: string }) => ({
            value: String(area.id),
            label: area.name,
          }))
          .sort((a: FilterOption, b: FilterOption) => a.label.localeCompare(b.label));

        const orgOptions: FilterOption[] = (orgsData.results || [])
          .map((org: { id: number; name: string }) => ({
            value: String(org.id),
            label: org.name,
          }))
          .sort((a: FilterOption, b: FilterOption) => a.label.localeCompare(b.label));

        setAreas(areaOptions);
        setOrganisations(orgOptions);
      } catch (err) {
        console.error('Error fetching filter options:', err);
        setError(err instanceof Error ? err.message : 'Failed to load filter options');
      } finally {
        setIsLoading(false);
      }
    };

    fetchOptions();
  }, []);

  return {
    areas,
    organisations,
    isLoading,
    error,
  };
}
