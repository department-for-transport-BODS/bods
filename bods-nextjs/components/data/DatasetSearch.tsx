'use client';

/**
 * Dataset Search Component
 *
 *
 * Search input for filtering datasets by keyword.
 * Matches against dataset name, operator, and description.
 * Updates URL with search query parameter.
 *
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';

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

export function DatasetSearch({
  onSearch,
  placeholder = 'Search by name, operator or description',
  label = 'Search datasets',
  hint = 'Enter keywords to search for datasets by name, operator or description',
}: DatasetSearchProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const initialSearch = searchParams.get('search') || '';
  const [searchValue, setSearchValue] = useState(initialSearch);
  const [isSearching, setIsSearching] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const announcementRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const urlSearch = searchParams.get('search') || '';
    setSearchValue(urlSearch);
  }, [searchParams]);

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

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    setIsSearching(true);

    updateUrl(searchValue);

    if (onSearch) {
      onSearch(searchValue);
    }

    setTimeout(() => setIsSearching(false), 100);
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
    <div className="dataset-search" data-testid="dataset-search">
      <form onSubmit={handleSubmit} role="search" aria-label="Search datasets">
        <div className="govuk-form-group">
          <label className="govuk-label govuk-label--m" htmlFor="dataset-search-input">
            {label}
          </label>
          <div id="dataset-search-hint" className="govuk-hint">
            {hint}
          </div>

          <div className="dataset-search__input-wrapper">
            <input
              ref={inputRef}
              type="search"
              id="dataset-search-input"
              name="search"
              className="govuk-input dataset-search__input"
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
                className="dataset-search__clear"
                onClick={handleClear}
                aria-label="Clear search"
              >
                <span aria-hidden="true">×</span>
              </button>
            )}

            <button
              type="submit"
              className="govuk-button dataset-search__button"
              data-module="govuk-button"
              disabled={isSearching}
              aria-label={isSearching ? 'Searching...' : 'Search'}
            >
              {isSearching ? 'Searching...' : 'Search'}
            </button>
          </div>
        </div>
      </form>

      <div
        ref={announcementRef}
        className="govuk-visually-hidden"
        role="status"
        aria-live="polite"
        aria-atomic="true"
      >
        {isSearching && 'Searching...'}
      </div>

      <style jsx>{`
        .dataset-search {
          margin-bottom: 30px;
        }

        .dataset-search__input-wrapper {
          display: flex;
          gap: 0;
          align-items: stretch;
        }

        .dataset-search__input {
          flex: 1;
          min-width: 0;
          border-right: none;
          border-top-right-radius: 0;
          border-bottom-right-radius: 0;
          margin-bottom: 0;
        }

        .dataset-search__input:focus {
          z-index: 1;
        }

        .dataset-search__clear {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 40px;
          background: #fff;
          border: 2px solid #0b0c0c;
          border-left: none;
          border-right: none;
          cursor: pointer;
          font-size: 24px;
          line-height: 1;
          color: #505a5f;
          padding: 0;
        }

        .dataset-search__clear:hover {
          background: #f3f2f1;
          color: #0b0c0c;
        }

        .dataset-search__clear:focus {
          outline: 3px solid #ffdd00;
          outline-offset: 0;
          z-index: 1;
        }

        .dataset-search__button {
          margin-bottom: 0;
          border-top-left-radius: 0;
          border-bottom-left-radius: 0;
          white-space: nowrap;
        }

        @media (max-width: 640px) {
          .dataset-search__input-wrapper {
            flex-wrap: wrap;
          }

          .dataset-search__input {
            flex: 1 1 100%;
            border-right: 2px solid #0b0c0c;
            border-radius: 0;
            margin-bottom: 10px;
          }

          .dataset-search__clear {
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            border: none;
            background: transparent;
            width: auto;
            height: auto;
          }

          .dataset-search__button {
            width: 100%;
            border-radius: 0;
          }
        }
      `}</style>
    </div>
  );
}

