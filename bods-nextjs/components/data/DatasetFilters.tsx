/**
 * Dataset Filters Component
 *
 *
 * Provides filtering UI for datasets by:
 * - Region (AdminArea)
 * - Operator (Organisation)
 * - Data Type (Timetables, AVL, Fares)
 * - Status (Published, Inactive)
 *
 * Matches Django implementation from transit_odp/browse/forms.py
 */

'use client';

import { useState, useCallback } from 'react';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import styles from './DatasetFilters.module.css';

export interface FilterOption {
  value: string;
  label: string;
}

export interface FilterValues {
  area?: string;
  organisation?: string;
  status?: string;
  dataType?: string;
}

interface DatasetFiltersProps {
  /** Available region/admin area options */
  areas?: FilterOption[];
  /** Available operator/organisation options */
  organisations?: FilterOption[];
  /** Callback when filters change */
  onFilterChange?: (filters: FilterValues) => void;
  /** Loading state while fetching filter options */
  isLoading?: boolean;
}

const STATUS_OPTIONS: FilterOption[] = [
  { value: '', label: 'All statuses' },
  { value: 'live', label: 'Published' },
  { value: 'inactive', label: 'Inactive' },
];

const DATA_TYPE_OPTIONS: FilterOption[] = [
  { value: '', label: 'All data types' },
  { value: '1', label: 'Timetables' },
  { value: '2', label: 'Automatic Vehicle Locations' },
  { value: '3', label: 'Fares' },
];

export function DatasetFilters({
  areas = [],
  organisations = [],
  onFilterChange,
  isLoading = false,
}: DatasetFiltersProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const urlFilters = {
    area: searchParams.get('area') || '',
    organisation: searchParams.get('organisation') || '',
    status: searchParams.get('status') || '',
    dataType: searchParams.get('dataType') || '',
  };

  const [filters, setFilters] = useState<FilterValues>(urlFilters);
  const [searchOrganisationTerm, setSearchOrganisationTerm] = useState('');

  const updateUrl = useCallback((newFilters: FilterValues) => {
    const params = new URLSearchParams(searchParams.toString());

    Object.entries(newFilters).forEach(([key, value]) => {
      if (value && value !== '') {
        params.set(key, value);
      } else {
        params.delete(key);
      }
    });

    params.delete('page');

    const queryString = params.toString();
    router.push(queryString ? `${pathname}?${queryString}` : pathname);
  }, [pathname, router, searchParams]);

  const handleFilterChange = useCallback((
    filterName: keyof FilterValues,
    value: string
  ) => {
    const newFilters = {
      ...filters,
      [filterName]: value,
    };

    setFilters(newFilters);
    updateUrl(newFilters);

    if (onFilterChange) {
      onFilterChange(newFilters);
    }
  }, [filters, updateUrl, onFilterChange]);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    updateUrl(filters);

    if (onFilterChange) {
      onFilterChange(filters);
    }
  }, [filters, updateUrl, onFilterChange]);

  const handleClearAll = useCallback(() => {
    const clearedFilters: FilterValues = {
      area: '',
      organisation: '',
      status: '',
      dataType: '',
    };

    setFilters(clearedFilters);
    updateUrl(clearedFilters);

    if (onFilterChange) {
      onFilterChange(clearedFilters);
    }
  }, [updateUrl, onFilterChange]);

  const filteredOrganisations = organisations.filter(org =>
    org.label.toLowerCase().includes(searchOrganisationTerm.toLowerCase())
  );

  const hasActiveFilters = Object.values(urlFilters).some(value => value && value !== '');

  return (
    <div className={`${styles['dataset-filters']}`}>
      <h2 className="govuk-heading-m">Filter by</h2>

      <form onSubmit={handleSubmit} noValidate>
        <div className="govuk-form-group">
          <label
            className="govuk-label"
            htmlFor="filter-area"
          >
            Geographical area
          </label>
          <select
            id="filter-area"
            name="area"
            className="govuk-select govuk-!-width-full"
            value={filters.area || urlFilters.area}
            onChange={(e) => handleFilterChange('area', e.target.value)}
            disabled={isLoading}
          >
            <option value="">All geographical areas</option>
            {areas.map((area) => (
              <option key={area.value} value={area.value}>
                {area.label}
              </option>
            ))}
          </select>
        </div>

        <div className="govuk-form-group">
          <label
            className="govuk-label"
            htmlFor="filter-organisation"
          >
            Publisher
          </label>
          {organisations.length > 10 && (
            <input
              type="text"
              className="govuk-input govuk-!-width-full govuk-!-margin-bottom-2"
              placeholder="Search publishers..."
              value={searchOrganisationTerm}
              onChange={(e) => setSearchOrganisationTerm(e.target.value)}
              aria-label="Search publishers"
            />
          )}
          <select
            id="filter-organisation"
            name="organisation"
            className="govuk-select govuk-!-width-full"
            value={filters.organisation || urlFilters.organisation}
            onChange={(e) => handleFilterChange('organisation', e.target.value)}
            disabled={isLoading}
          >
            <option value="">All publishers</option>
            {filteredOrganisations.map((org) => (
              <option key={org.value} value={org.value}>
                {org.label}
              </option>
            ))}
          </select>
        </div>

        <div className="govuk-form-group">
          <label
            className="govuk-label"
            htmlFor="filter-status"
          >
            Status
          </label>
          <select
            id="filter-status"
            name="status"
            className="govuk-select govuk-!-width-full"
            value={filters.status || urlFilters.status}
            onChange={(e) => handleFilterChange('status', e.target.value)}
            disabled={isLoading}
          >
            {STATUS_OPTIONS.map((status) => (
              <option key={status.value} value={status.value}>
                {status.label}
              </option>
            ))}
          </select>
        </div>

        <div className="govuk-form-group">
          <label
            className="govuk-label"
            htmlFor="filter-dataType"
          >
            Data type
          </label>
          <select
            id="filter-dataType"
            name="dataType"
            className="govuk-select govuk-!-width-full"
            value={filters.dataType || urlFilters.dataType}
            onChange={(e) => handleFilterChange('dataType', e.target.value)}
            disabled={isLoading}
          >
            {DATA_TYPE_OPTIONS.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          className="govuk-button"
          data-module="govuk-button"
          disabled={isLoading}
        >
          Apply filter
        </button>

        {hasActiveFilters && (
          <button
            type="button"
            className="govuk-button govuk-button--secondary govuk-!-margin-top-2"
            onClick={handleClearAll}
            disabled={isLoading}
          >
            Clear all filters
          </button>
        )}
      </form>
    </div>
  );
}
