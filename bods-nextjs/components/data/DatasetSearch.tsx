/**
 * Dataset Search Component
 *
 *
 * Search input for filtering datasets by keyword.
 * Matches against dataset name, operator, and description.
 * Updates URL with search query parameter.
 *
 */

'use client';

import { useState, useCallback, useRef } from 'react';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import styles from './DatasetSearch.module.css';

interface DatasetSearchProps {
  /** Callback when search is submitted */
  onSearch?: (query: string) => void;
  /** Placeholder text for the search input */
  placeholder?: string;
  /** Label for the search input (visible) */
  label?: string;
  /** Hint text below the label */
  hint?: string;
}

interface DatasetSearchFormProps extends DatasetSearchProps {
  /** Search query from the current URL */
  initialSearch: string;
  /** Pushes the updated search query into the URL */
  updateUrl: (query: string) => void;
}

function DatasetSearchForm({
  initialSearch,
  updateUrl,
  onSearch,
  placeholder,
  label,
  hint,
}: DatasetSearchFormProps) {
  const [searchValue, setSearchValue] = useState(initialSearch);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    updateUrl(searchValue);

    if (onSearch) {
      onSearch(searchValue);
    }
  }, [searchValue, updateUrl, onSearch]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchValue(e.target.value);
  }, []);

  const handleClear = useCallback(() => {
    setSearchValue('');
    updateUrl('');

    if (onSearch) {
      onSearch('');
    }

    inputRef.current?.focus();
  }, [updateUrl, onSearch]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape' && searchValue) {
      e.preventDefault();
      handleClear();
    }
  }, [searchValue, handleClear]);

  const hasSearchValue = searchValue.trim().length > 0;

  return (
    <div className={styles.datasetSearch}>
      <form onSubmit={handleSubmit} role="search" aria-label="Search datasets">
        <div className="govuk-form-group">
          <label className="govuk-label govuk-label--m" htmlFor="dataset-search-input">
            {label}
          </label>
          <div id="dataset-search-hint" className="govuk-hint">
            {hint}
          </div>

          <div className={styles.inputWrapper}>
            <input
              ref={inputRef}
              type="search"
              id="dataset-search-input"
              name="search"
              className={`govuk-input ${styles.input}`}
              placeholder={placeholder}
              value={searchValue}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              aria-describedby="dataset-search-hint"
              autoComplete="off"
              spellCheck="false"
            />

            {hasSearchValue && (
              <button
                type="button"
                className={styles.clearButton}
                onClick={handleClear}
                aria-label="Clear search"
              >
                <span aria-hidden="true">×</span>
              </button>
            )}

            <button
              type="submit"
              className={`govuk-button ${styles.button}`}
              data-module="govuk-button"
              aria-label="Search"
            >
              Search
            </button>
          </div>
        </div>
      </form>

      <div
        className="govuk-visually-hidden"
        role="status"
        aria-live="polite"
        aria-atomic="true"
      />
    </div>
  );
}

export function DatasetSearch({
  onSearch,
  placeholder = 'Search by name, operator or description',
  label = 'Search datasets',
  hint = 'Enter keywords to search for datasets by name, operator or description',
}: DatasetSearchProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const currentUrlSearch = searchParams.get('search') || '';

  const updateUrl = useCallback((query: string) => {
    const params = new URLSearchParams(searchParams.toString());

    if (query.trim()) {
      params.set('search', query.trim());
      params.delete('page');
    } else {
      params.delete('search');
      params.delete('page');
    }

    const queryString = params.toString();
    router.push(queryString ? `${pathname}?${queryString}` : pathname);
  }, [pathname, router, searchParams]);

  return (
    <DatasetSearchForm
      key={currentUrlSearch}
      initialSearch={currentUrlSearch}
      updateUrl={updateUrl}
      onSearch={onSearch}
      placeholder={placeholder}
      label={label}
      hint={hint}
    />
  );
}

