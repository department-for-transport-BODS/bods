'use client';

/**
 * Active Filter Tags Component
 *
 *
 * Displays active filters as removable tags/pills.
 * Matches Django template: transit_odp/browse/templates/browse/snippets/search_list.html
 *
 */

import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import { useCallback } from 'react';
import Image from 'next/image';
import type { FilterOption } from './DatasetFilters';
import styles from './DatasetFilters.module.css';

interface ActiveFilterTagsProps {
  /** Available area options for label lookup */
  areas?: FilterOption[];
  /** Available organisation options for label lookup */
  organisations?: FilterOption[];
}

const STATUS_LABELS: Record<string, string> = {
  'live': 'Published',
  'inactive': 'Inactive',
};

const DATA_TYPE_LABELS: Record<string, string> = {
  '1': 'Timetables',
  '2': 'Automatic Vehicle Locations',
  '3': 'Fares',
};

export function ActiveFilterTags({
  areas = [],
  organisations = [],
}: ActiveFilterTagsProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const activeFilters: Array<{ key: string; value: string; label: string }> = [];

  const getLabel = (key: string, value: string): string => {
    switch (key) {
      case 'area':
        return areas.find(a => a.value === value)?.label || value;
      case 'organisation':
        return organisations.find(o => o.value === value)?.label || value;
      case 'status':
        return STATUS_LABELS[value] || value;
      case 'dataType':
        return DATA_TYPE_LABELS[value] || value;
      default:
        return value;
    }
  };

  const filterKeys = ['area', 'organisation', 'status', 'dataType'];
  filterKeys.forEach(key => {
    const value = searchParams.get(key);
    if (value) {
      activeFilters.push({
        key,
        value,
        label: getLabel(key, value),
      });
    }
  });

  const removeFilter = useCallback((filterKey: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.delete(filterKey);
    params.delete('page'); // Reset to page 1

    const queryString = params.toString();
    router.push(queryString ? `${pathname}?${queryString}` : pathname);
  }, [pathname, router, searchParams]);

  const clearAllFilters = useCallback(() => {
    const params = new URLSearchParams(searchParams.toString());

    const search = params.get('search');
    params.delete('area');
    params.delete('organisation');
    params.delete('status');
    params.delete('dataType');
    params.delete('page');

    const newParams = new URLSearchParams();
    if (search) {
      newParams.set('search', search);
    }

    const queryString = newParams.toString();
    router.push(queryString ? `${pathname}?${queryString}` : pathname);
  }, [pathname, router, searchParams]);

  if (activeFilters.length === 0) {
    return null;
  }

  return (
    <div
      className={`govuk-body-s ${styles['search-pillbox']}`}
      data-testid="active-filter-tags"
      role="region"
      aria-label="Active filters"
    >
      <div className="govuk-!-margin-bottom-2">
        <span className="govuk-label govuk-!-font-weight-bold govuk-!-margin-right-2">
          Active filters:
        </span>
      </div>

      <div className={styles['filter-tags']}>
        {activeFilters.map(({ key, label }) => (
          <button
            key={key}
            type="button"
            className={styles['pill-item']}
            onClick={() => removeFilter(key)}
            aria-label={`Remove filter: ${label}`}
          >
            <span className={styles['pill-item__label']}>{label}</span>
            <Image
              className={styles['pill-item__image']}
              src="/static/frontend/images/icon-cross.png"
              alt=""
              height={16}
              width={16}
              aria-hidden="true"
            />
          </button>
        ))}

        {activeFilters.length > 1 && (
          <button
            type="button"
            className="govuk-link govuk-!-margin-left-2"
            onClick={clearAllFilters}
            aria-label="Clear all filters"
          >
            Clear all
          </button>
        )}
      </div>

      <hr className={`govuk-section-break govuk-section-break--s govuk-section-break--visible ${styles['pillbox-break']}`} />
    </div>
  );
}
