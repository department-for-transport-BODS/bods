'use client';

/**
 * Pagination Component
 * Review this - potentially a better way of doing this!
 */

import Link from 'next/link';
import { useSearchParams, usePathname } from 'next/navigation';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalResults?: number;
  resultsPerPage?: number;
  onPageChange?: (page: number) => void;
  pageParam?: string;
  baseUrl?: string;
}

export function Pagination({
  currentPage,
  totalPages,
  totalResults,
  resultsPerPage,
  onPageChange,
  pageParam = 'page',
  baseUrl,
}: PaginationProps) {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const isUrlMode = !onPageChange;
  const effectiveBaseUrl = baseUrl || pathname;

  const createPageUrl = (page: number) => {
    const params = new URLSearchParams(searchParams.toString());
    if (page === 1) {
      params.delete(pageParam);
    } else {
      params.set(pageParam, page.toString());
    }
    const queryString = params.toString();
    return queryString ? `${effectiveBaseUrl}?${queryString}` : effectiveBaseUrl;
  };

  const handlePageClick = (page: number, e: React.MouseEvent) => {
    if (onPageChange) {
      e.preventDefault();
      onPageChange(page);
    }
  };

  const getPageRange = () => {
    const range: number[] = [];
    const start = Math.max(1, currentPage - 2);
    const end = Math.min(totalPages, currentPage + 2);

    for (let i = start; i <= end; i++) {
      range.push(i);
    }
    return range;
  };

  if (totalPages <= 1) {
    return null;
  }

  const pageRange = getPageRange();
  const showStartEllipsis = pageRange[0] > 2;
  const showEndEllipsis = pageRange[pageRange.length - 1] < totalPages - 1;

  const startResult = resultsPerPage ? (currentPage - 1) * resultsPerPage + 1 : null;
  const endResult = resultsPerPage && totalResults
    ? Math.min(currentPage * resultsPerPage, totalResults)
    : null;

  return (
    <nav className="govuk-pagination" aria-label="Pagination">
      {totalResults && resultsPerPage && (
        <p className="govuk-body govuk-!-margin-bottom-4">
          Showing {startResult} to {endResult} of {totalResults} results
        </p>
      )}

      <div className="govuk-pagination__prev">
        {currentPage > 1 ? (
          isUrlMode ? (
            <Link
              href={createPageUrl(currentPage - 1)}
              className="govuk-link govuk-pagination__link"
              rel="prev"
              aria-label="Go to previous page"
            >
              <svg className="govuk-pagination__icon govuk-pagination__icon--prev" xmlns="http://www.w3.org/2000/svg" height="13" width="15" aria-hidden="true" focusable="false" viewBox="0 0 15 13">
                <path d="m6.5938-0.0078125-6.7266 6.7266 6.7441 6.4062 1.377-1.449-4.1856-3.9768h12.896v-2h-12.984l4.2931-4.293-1.414-1.414z"></path>
              </svg>
              <span className="govuk-pagination__link-title">
                Previous<span className="govuk-visually-hidden"> page</span>
              </span>
            </Link>
          ) : (
            <button
              type="button"
              className="govuk-link govuk-pagination__link"
              onClick={(e) => handlePageClick(currentPage - 1, e)}
              aria-label="Go to previous page"
            >
              <svg className="govuk-pagination__icon govuk-pagination__icon--prev" xmlns="http://www.w3.org/2000/svg" height="13" width="15" aria-hidden="true" focusable="false" viewBox="0 0 15 13">
                <path d="m6.5938-0.0078125-6.7266 6.7266 6.7441 6.4062 1.377-1.449-4.1856-3.9768h12.896v-2h-12.984l4.2931-4.293-1.414-1.414z"></path>
              </svg>
              <span className="govuk-pagination__link-title">
                Previous<span className="govuk-visually-hidden"> page</span>
              </span>
            </button>
          )
        ) : null}
      </div>

      <ul className="govuk-pagination__list">
        {pageRange[0] > 1 && (
          <li className="govuk-pagination__item">
            {isUrlMode ? (
              <Link
                href={createPageUrl(1)}
                className="govuk-link govuk-pagination__link"
                aria-label="Go to page 1"
              >
                1
              </Link>
            ) : (
              <button
                type="button"
                className="govuk-link govuk-pagination__link"
                onClick={(e) => handlePageClick(1, e)}
                aria-label="Go to page 1"
              >
                1
              </button>
            )}
          </li>
        )}

        {showStartEllipsis && (
          <li className="govuk-pagination__item govuk-pagination__item--ellipses">
            &ctdot;
          </li>
        )}

        {pageRange.map((page) => (
          <li
            key={page}
            className={`govuk-pagination__item ${page === currentPage ? 'govuk-pagination__item--current' : ''}`}
          >
            {page === currentPage ? (
              <span
                className="govuk-pagination__link"
                aria-current="page"
                aria-label={`Page ${page}, current page`}
              >
                {page}
              </span>
            ) : isUrlMode ? (
              <Link
                href={createPageUrl(page)}
                className="govuk-link govuk-pagination__link"
                aria-label={`Go to page ${page}`}
              >
                {page}
              </Link>
            ) : (
              <button
                type="button"
                className="govuk-link govuk-pagination__link"
                onClick={(e) => handlePageClick(page, e)}
                aria-label={`Go to page ${page}`}
              >
                {page}
              </button>
            )}
          </li>
        ))}

        {showEndEllipsis && (
          <li className="govuk-pagination__item govuk-pagination__item--ellipses">
            &ctdot;
          </li>
        )}

        {pageRange[pageRange.length - 1] < totalPages && (
          <li className="govuk-pagination__item">
            {isUrlMode ? (
              <Link
                href={createPageUrl(totalPages)}
                className="govuk-link govuk-pagination__link"
                aria-label={`Go to page ${totalPages}`}
              >
                {totalPages}
              </Link>
            ) : (
              <button
                type="button"
                className="govuk-link govuk-pagination__link"
                onClick={(e) => handlePageClick(totalPages, e)}
                aria-label={`Go to page ${totalPages}`}
              >
                {totalPages}
              </button>
            )}
          </li>
        )}
      </ul>

      <div className="govuk-pagination__next">
        {currentPage < totalPages ? (
          isUrlMode ? (
            <Link
              href={createPageUrl(currentPage + 1)}
              className="govuk-link govuk-pagination__link"
              rel="next"
              aria-label="Go to next page"
            >
              <span className="govuk-pagination__link-title">
                Next<span className="govuk-visually-hidden"> page</span>
              </span>
              <svg className="govuk-pagination__icon govuk-pagination__icon--next" xmlns="http://www.w3.org/2000/svg" height="13" width="15" aria-hidden="true" focusable="false" viewBox="0 0 15 13">
                <path d="m8.107-0.0078125-1.4136 1.414 4.2926 4.293h-12.986v2h12.896l-4.1855 3.9766 1.377 1.4492 6.7441-6.4062-6.7246-6.7266z"></path>
              </svg>
            </Link>
          ) : (
            <button
              type="button"
              className="govuk-link govuk-pagination__link"
              onClick={(e) => handlePageClick(currentPage + 1, e)}
              aria-label="Go to next page"
            >
              <span className="govuk-pagination__link-title">
                Next<span className="govuk-visually-hidden"> page</span>
              </span>
              <svg className="govuk-pagination__icon govuk-pagination__icon--next" xmlns="http://www.w3.org/2000/svg" height="13" width="15" aria-hidden="true" focusable="false" viewBox="0 0 15 13">
                <path d="m8.107-0.0078125-1.4136 1.414 4.2926 4.293h-12.986v2h12.896l-4.1855 3.9766 1.377 1.4492 6.7441-6.4062-6.7246-6.7266z"></path>
              </svg>
            </button>
          )
        ) : null}
      </div>
    </nav>
  );
}

