'use client';

/**
 * Data Quality Badge Component
 *
 *
 * Displays data quality score with RAG indicator (green/amber/red).:
 * - Score thresholds: GREEN ≥ 100%, AMBER > 90%, RED ≤ 90%
 * - Visual indicator with colored dot
 * - Percentage score (e.g., "85%")
 * - RAG level text (GREEN/AMBER/RED)

 */

import Link from 'next/link';
import type { DataQualityRag } from '@/types';

export interface DataQualityBadgeProps {
  /** Score as percentage string (e.g., "85.5%") */
  score: string;
  /** RAG indicator: green, amber, red, or unavailable */
  rag: DataQualityRag;
  /** Optional: Link to full quality report */
  reportUrl?: string;
  /** Optional: Show as inline (for lists) or stacked (for detail pages) */
  variant?: 'inline' | 'stacked';
  /** Optional: Size of badge */
  size?: 'small' | 'medium' | 'large';
  /** Optional: Show tooltip on hover */
  showTooltip?: boolean;
}

/**
 * Get the RAG level display text
 */
function getRagLevelText(rag: DataQualityRag): string {
  switch (rag) {
    case 'green':
      return 'GREEN';
    case 'amber':
      return 'AMBER';
    case 'red':
      return 'RED';
    case 'unavailable':
    default:
      return 'UNAVAILABLE';
  }
}

/**
 * Get the CSS class for the status indicator dot color
 * Matches Django: status-indicator--success/warning/error
 */
function getIndicatorClass(rag: DataQualityRag): string {
  switch (rag) {
    case 'green':
      return 'success';
    case 'amber':
      return 'warning';
    case 'red':
      return 'error';
    case 'unavailable':
    default:
      return 'unavailable';
  }
}

/**
 * Get the background color for the indicator dot
 */
function getIndicatorColor(rag: DataQualityRag): string {
  switch (rag) {
    case 'green':
      return '#006435'; // GDS green
    case 'amber':
      return '#ffbf47'; // GDS yellow/warning
    case 'red':
      return '#b10e1e'; // GDS red/error
    case 'unavailable':
    default:
      return '#f47738'; // GDS orange
  }
}

/**
 * Get tooltip text explaining the quality score
 */
function getTooltipText(rag: DataQualityRag, score: string): string {
  if (rag === 'unavailable') {
    return 'Data quality score is currently unavailable for this dataset';
  }

  if (rag === 'green') {
    return `This dataset has a high quality score of ${score}. It meets all required standards and has minimal issues.`;
  } else if (rag === 'amber') {
    return `This dataset has a moderate quality score of ${score}. There may be some minor issues that should be reviewed.`;
  } else {
    return `This dataset has a low quality score of ${score}. There are issues that need attention before using this data.`;
  }
}

/**
 * Get accessible label for screen readers
 */
function getAriaLabel(rag: DataQualityRag, score: string): string {
  if (rag === 'unavailable') {
    return 'Data quality score unavailable';
  }

  const ragText = getRagLevelText(rag);
  return `Data quality score: ${score}, rated ${ragText}`;
}

export function DataQualityBadge({
  score,
  rag,
  reportUrl,
  variant = 'inline',
  size = 'medium',
  showTooltip = true,
}: DataQualityBadgeProps) {
  if (rag === 'unavailable') {
    return null;
  }

  const indicatorClass = getIndicatorClass(rag);
  const indicatorColor = getIndicatorColor(rag);
  const ragText = getRagLevelText(rag);
  const tooltipText = getTooltipText(rag, score);
  const ariaLabel = getAriaLabel(rag, score);

  const content = (
    <span
      className={`status-indicator status-indicator--${indicatorClass} govuk-!-font-weight-bold`}
      aria-label={ariaLabel}
      title={showTooltip ? tooltipText : undefined}
      style={{
        fontFamily: '"GDS Transport", Arial, sans-serif',
        fontSize: size === 'small' ? '0.875rem' : size === 'large' ? '1.25rem' : 'inherit',
        whiteSpace: 'nowrap',
        display: variant === 'stacked' ? 'block' : 'inline',
      }}
    >
      {score} {ragText}
      <style jsx>{`
        .status-indicator {
          font-family: "GDS Transport", Arial, sans-serif;
          font-size: inherit;
          white-space: nowrap;
          position: relative;
        }

        .status-indicator:before {
          content: " ";
          display: inline-block;
          width: 1.125rem;
          height: 1.125rem;
          border-radius: 50%;
          margin: 0 0.4rem 0 0.2rem;
          background-color: ${indicatorColor};
          vertical-align: middle;
        }

        .status-indicator--success:before {
          background-color: #006435;
        }

        .status-indicator--warning:before {
          background-color: #ffbf47;
        }

        .status-indicator--error:before {
          background-color: #b10e1e;
        }

        .status-indicator--unavailable:before {
          background-color: #f47738;
        }
      `}</style>
    </span>
  );

  if (variant === 'stacked') {
    return (
      <div className="dq-badge-stacked">
        <div style={{ marginBottom: '0.25rem' }}>Data quality</div>
        {reportUrl ? (
          <Link
            href={reportUrl}
            className="govuk-link"
            target="_blank"
            rel="noopener noreferrer"
            aria-label={`View full data quality report (${ariaLabel})`}
          >
            {content}
          </Link>
        ) : (
          content
        )}
      </div>
    );
  }

  if (reportUrl) {
    return (
      <Link
        href={reportUrl}
        className="govuk-link"
        target="_blank"
        rel="noopener noreferrer"
        aria-label={`View full data quality report (${ariaLabel})`}
      >
        {content}
      </Link>
    );
  }

  return content;
}
