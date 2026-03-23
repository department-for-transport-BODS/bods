/**
 * Dataset Card Component
 *
 *
 * Displays a single dataset in the listing with:
 * - Dataset name
 * - Data type indicator
 * - Operator name
 * - Last updated date
 * - Data quality score badge
 *
 */

'use client';

import Link from 'next/link';
import type { DatasetListItem, DatasetType } from '@/types';
import { DataQualityBadge } from './DataQualityBadge';
import styles from './DatasetCard.module.css';

interface DatasetCardProps {
  dataset: DatasetListItem;
}

/**
 * Get the data type display label
 */
function getDataTypeLabel(dataType?: DatasetType): string {
  switch (dataType) {
    case 'TIMETABLE':
      return 'Timetable';
    case 'AVL':
      return 'Location';
    case 'FARES':
      return 'Fares';
    default:
      return 'Timetable';
  }
}

/**
 * Get the appropriate GDS tag class for data type
 */
function getDataTypeClass(dataType?: DatasetType): string {
  switch (dataType) {
    case 'TIMETABLE':
      return 'govuk-tag govuk-tag--blue';
    case 'AVL':
      return 'govuk-tag govuk-tag--purple';
    case 'FARES':
      return 'govuk-tag govuk-tag--turquoise';
    default:
      return 'govuk-tag govuk-tag--blue';
  }
}

/**
 * Format a date string to a human-readable format
 */
function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
  } catch {
    return 'Unknown date';
  }
}

export function DatasetCard({ dataset }: DatasetCardProps) {
  const dataTypeLabel = getDataTypeLabel(dataset.dataType);
  const dataTypeClass = getDataTypeClass(dataset.dataType);
  const formattedDate = formatDate(dataset.modified);

  return (
    <div className={styles.datasetCard}>
      <div className="govuk-summary-card">
        <div className="govuk-summary-card__title-wrapper">
          <h2 className="govuk-summary-card__title">
            <Link
              href={`/data/${dataset.id}`}
              className="govuk-link"
              aria-label={`View details for ${dataset.name}`}
            >
              {dataset.name}
            </Link>
          </h2>
          <div className="govuk-summary-card__actions">
            <span
              className={dataTypeClass}
              aria-label={`Data type: ${dataTypeLabel}`}
            >
              {dataTypeLabel}
            </span>
          </div>
        </div>
        <div className="govuk-summary-card__content">
          <dl className="govuk-summary-list">
            <div className="govuk-summary-list__row">
              <dt className="govuk-summary-list__key">Operator</dt>
              <dd className="govuk-summary-list__value">{dataset.operatorName}</dd>
            </div>
            <div className="govuk-summary-list__row">
              <dt className="govuk-summary-list__key">Last updated</dt>
              <dd className="govuk-summary-list__value">
                <time dateTime={dataset.modified}>{formattedDate}</time>
              </dd>
            </div>
            <div className="govuk-summary-list__row">
              <dt className="govuk-summary-list__key">Data quality</dt>
              <dd className="govuk-summary-list__value">
                <DataQualityBadge
                  score={dataset.dqScore}
                  rag={dataset.dqRag}
                  variant="inline"
                  size="small"
                />
              </dd>
            </div>
            {dataset.description && (
              <div className="govuk-summary-list__row">
                <dt className="govuk-summary-list__key">Description</dt>
                <dd className="govuk-summary-list__value">
                  {dataset.description.length > 150
                    ? `${dataset.description.substring(0, 150)}...`
                    : dataset.description}
                </dd>
              </div>
            )}
          </dl>
        </div>
      </div>
    </div>
  );
}

