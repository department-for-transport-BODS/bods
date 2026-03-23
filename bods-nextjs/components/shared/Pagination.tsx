/**
 * Pagination Component
 * Review this - potentially a better way of doing this!
 */

'use client';

import Link from 'next/link';
import { useSearchParams, usePathname } from 'next/navigation';
import { PaginationPrevIcon, PaginationNextIcon } from './PaginationIcons';

function PaginationNavButton({
  page,
  direction,
  isUrlMode,
  createPageUrl,
  handlePageClick,
}: {
  page: number;
  direction: 'prev' | 'next';
  isUrlMode: boolean;
  createPageUrl: (page: number) => string;
  handlePageClick: (page: number, e: React.MouseEvent) => void;
}) {
  const label = direction === 'prev' ? 'Previous' : 'Next';
  const ariaLabel = `Go to ${label.toLowerCase()} page`;
  const rel = direction === 'prev' ? 'prev' : 'next';
  const icon = direction === 'prev' ? PaginationPrevIcon : PaginationNextIcon;

  const content = direction === 'prev' ? (
    <>
      {icon}
      <span className="govuk-pagination__link-title">
        {label}<span className="govuk-visually-hidden"> page</span>
      </span>
    </>
  ) : (
    <>
      <span className="govuk-pagination__link-title">
        {label}<span className="govuk-visually-hidden"> page</span>
      </span>
      {icon}
    </>
  );

  return isUrlMode ? (
    <Link href={createPageUrl(page)} className="govuk-link govuk-pagination__link" rel={rel} aria-label={ariaLabel}>
      {content}
    </Link>
  ) : (
    <button type="button" className="govuk-link govuk-pagination__link" onClick={(e) => handlePageClick(page, e)} aria-label={ariaLabel}>
      {content}
    </button>
  );
}

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
        {currentPage > 1 && (
          <PaginationNavButton
            page={currentPage - 1}
            direction="prev"
            isUrlMode={isUrlMode}
            createPageUrl={createPageUrl}
            handlePageClick={handlePageClick}
          />
        )}
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
        {currentPage < totalPages && (
          <PaginationNavButton
            page={currentPage + 1}
            direction="next"
            isUrlMode={isUrlMode}
            createPageUrl={createPageUrl}
            handlePageClick={handlePageClick}
          />
        )}
      </div>
    </nav>
  );
}

