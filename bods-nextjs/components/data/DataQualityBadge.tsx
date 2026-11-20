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

'use client';

import Link from 'next/link';
import type { DataQualityRag } from '@/types';
import styles from './DataQualityBadge.module.css';

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
 * Get tooltip text explaining the quality score
 */
function getTooltipText(rag: DataQualityRag, score: string): string {
  switch (rag) {
    case 'unavailable':
      return 'Data quality score is currently unavailable for this dataset';
    case 'green':
      return `This dataset has a high quality score of ${score}. It meets all required standards and has minimal issues.`;
    case 'amber':
      return `This dataset has a moderate quality score of ${score}. There may be some minor issues that should be reviewed.`;
    case 'red':
    default:
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
  const ragText = getRagLevelText(rag);
  const tooltipText = getTooltipText(rag, score);
  const ariaLabel = getAriaLabel(rag, score);
  const sizeClass = size === 'small' ? styles.sizeSmall : size === 'large' ? styles.sizeLarge : styles.sizeMedium;
  const variantClass = variant === 'stacked' ? styles.stacked : styles.inline;

  const content = (
    <span
      className={`${styles.statusIndicator} ${styles[indicatorClass]} ${sizeClass} ${variantClass} govuk-!-font-weight-bold`}
      aria-label={ariaLabel}
      title={showTooltip ? tooltipText : undefined}
    >
      {score} {ragText}
    </span>
  );

  if (variant === 'stacked') {
    return (
      <div className={styles.stackedWrapper}>
        <div className={styles.stackedLabel}>Data quality</div>
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
