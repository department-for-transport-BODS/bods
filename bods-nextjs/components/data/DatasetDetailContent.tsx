'use client';

/**
 * Dataset Detail Content Component
 *
 *
 * MIGRATION NOTE: Matches Django template structure
 * Source: transit_odp/browse/templates/browse/timetables/dataset_detail/success_content.html
 *        transit_odp/browse/templates/browse/base/property_table.html
 *
 * Displays comprehensive dataset information including:
 * - Dataset properties (name, type, ID, description, owner, status)
 * - TransXChange version
 * - Data quality score
 * - Last updated timestamp
 * - Geographic coverage
 * - Line information
 * - Download/subscribe actions
 * - API URL for programmatic access

 */

import { useState } from 'react';
import Link from 'next/link';
import type { Dataset } from '@/types';
import { DataQualityBadge } from './DataQualityBadge';
import { DownloadSubscribePanel } from './DownloadSubscribePanel';
import { ApiUrlPanel } from './ApiUrlPanel';
import { RouteMap } from './RouteMap';

interface DatasetDetailContentProps {
  dataset: Dataset;
}

export function DatasetDetailContent({ dataset }: DatasetDetailContentProps) {
  const [isSubscribed, setIsSubscribed] = useState(false);

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const day = date.getDate();
    const month = date.toLocaleString('en-GB', { month: 'short' });
    const year = date.getFullYear();
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${day} ${month} ${year} ${hours}:${minutes}`;
  };

  return (
    <div className="dataset-detail-content">
      {/* Property table - matches Django browse/base/property_table.html */}
      <table className="govuk-table consumer-property-table">
        <tbody className="govuk-table__body">
          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Name
            </th>
            <td colSpan={2} className="govuk-table__cell dont-break-out">
              {dataset.name}
            </td>
          </tr>

          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Data type
            </th>
            <td colSpan={2} className="govuk-table__cell dont-break-out">
              Timetables data
            </td>
          </tr>

          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Data set ID
            </th>
            <td colSpan={2} className="govuk-table__cell dont-break-out">
              {dataset.id}
            </td>
          </tr>

          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Description
            </th>
            <td colSpan={2} className="govuk-table__cell dont-break-out">
              {dataset.description || 'No description provided'}
            </td>
          </tr>

          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Owner
            </th>
            <td colSpan={2} className="govuk-table__cell dont-break-out">
              <div className="stacked">
                <Link
                  href={`/data?organisation=${dataset.id}&status=live`}
                  className="govuk-link"
                >
                  {dataset.operatorName}
                </Link>
                <span>Access all data uploaded by this publisher</span>
              </div>
            </td>
          </tr>

          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Status
            </th>
            <td colSpan={2} className="govuk-table__cell">
              <div className="flex-between">
                <span className={`govuk-tag ${
                  dataset.status === 'published' || dataset.status === 'live'
                    ? 'govuk-tag--green'
                    : dataset.status === 'inactive'
                    ? 'govuk-tag--red'
                    : 'govuk-tag--grey'
                }`}>
                  {dataset.status === 'published' || dataset.status === 'live'
                    ? 'Published'
                    : dataset.status.charAt(0).toUpperCase() + dataset.status.slice(1)}
                </span>
              </div>
            </td>
          </tr>

          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              TransXChange version
            </th>
            <td colSpan={2} className="govuk-table__cell">
              2.4
            </td>
          </tr>

          {dataset.dqRag !== 'unavailable' && (
            <tr className="govuk-table__row">
              <th scope="row" className="govuk-table__header">
                Data quality report
              </th>
              <td className="govuk-table__cell">
                <DataQualityBadge
                  score={dataset.dqScore}
                  rag={dataset.dqRag}
                  variant="stacked"
                  reportUrl={`/publish/org/${dataset.id}/data-quality/${dataset.id}`}
                />
              </td>
              <td className="govuk-table__cell">
                <a
                  className="govuk-link"
                  href={`/publish/org/${dataset.id}/data-quality/${dataset.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  View data quality report
                </a>
              </td>
            </tr>
          )}

          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Last updated
            </th>
            <td className="govuk-table__cell dont-break-out">
              {formatDate(dataset.modified)}
            </td>
            <td className="govuk-table__cell">
              <Link
                href={`/data/${dataset.id}/changelog`}
                className="govuk-link"
              >
                View change log
              </Link>
            </td>
          </tr>
        </tbody>
      </table>

      {dataset.adminAreas && dataset.adminAreas.length > 0 && (
        <div className="govuk-!-margin-top-6">
          <h2 className="govuk-heading-m">Geographic coverage</h2>
          <ul className="govuk-list govuk-list--bullet">
            {dataset.adminAreas.map((area, index) => (
              <li key={index}>{area.name}</li>
            ))}
          </ul>
        </div>
      )}

      {dataset.lines && dataset.lines.length > 0 && (
        <div className="govuk-!-margin-top-6">
          <h2 className="govuk-heading-m">Lines</h2>
          <p className="govuk-body">
            This dataset contains {dataset.lines.length} line{dataset.lines.length !== 1 ? 's' : ''}:
          </p>
          <ul className="govuk-list govuk-list--bullet">
            {dataset.lines.slice(0, 10).map((line, index) => (
              <li key={index}>{line}</li>
            ))}
            {dataset.lines.length > 10 && (
              <li>...and {dataset.lines.length - 10} more</li>
            )}
          </ul>
        </div>
      )}

      {/* TODO: Add revision_id to Dataset type and fetch from API */}
      {process.env.NEXT_PUBLIC_MAPBOX_TOKEN && (
        <div className="govuk-!-margin-top-6">
          <h2 className="govuk-heading-m">Route map</h2>
          <RouteMap
            revisionId={dataset.id}
            mapboxToken={process.env.NEXT_PUBLIC_MAPBOX_TOKEN}
            apiRoot={process.env.NEXT_PUBLIC_API_URL}
            ariaLabel={`Interactive map showing routes for ${dataset.name}`}
          />
        </div>
      )}

      <ApiUrlPanel
        apiUrl={dataset.url}
        datasetType="TIMETABLE"
      />

      <DownloadSubscribePanel
        datasetId={dataset.id}
        downloadUrl={dataset.url}
        fileExtension={dataset.extension}
        isSubscribed={isSubscribed}
        onSubscribeToggle={async (subscribed) => {
          // TODO: Implement actual subscription API call
          setIsSubscribed(subscribed);
          console.log('Subscribe toggle:', subscribed);
        }}
      />
    </div>
  );
}
