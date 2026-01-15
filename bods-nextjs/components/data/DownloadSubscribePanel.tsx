'use client';

/**
 * Download and Subscribe Panel Component
 *
 *
 * MIGRATION NOTE: Matches Django template
 * Source: transit_odp/browse/templates/browse/base/subscribe_and_download.html
 *
 * Displays download and subscription options for datasets:
 * - Subscribe/unsubscribe toggle
 * - Download dataset file with extension display
 * - File size information (when available)
 * - Proper GDS button styling
 *
 */

import { useState } from 'react';
import Link from 'next/link';

export interface DownloadSubscribePanelProps {
  datasetId: number;
  downloadUrl: string;
  fileExtension: string;
  fileSize?: string;
  isSubscribed?: boolean;
  onSubscribeToggle?: (subscribed: boolean) => Promise<void>;
}

/**
 * Format file size for display
 */
function formatFileSize(bytes?: number): string {
  if (!bytes) return '';

  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return `${size.toFixed(1)} ${units[unitIndex]}`;
}

export function DownloadSubscribePanel({
  datasetId,
  downloadUrl,
  fileExtension,
  fileSize,
  isSubscribed = false,
  onSubscribeToggle,
}: DownloadSubscribePanelProps) {
  const [subscribed, setSubscribed] = useState(isSubscribed);
  const [isToggling, setIsToggling] = useState(false);

  const handleSubscribeToggle = async () => {
    if (!onSubscribeToggle) return;

    setIsToggling(true);
    try {
      await onSubscribeToggle(!subscribed);
      setSubscribed(!subscribed);
    } catch (error) {
      console.error('Failed to toggle subscription:', error);
    } finally {
      setIsToggling(false);
    }
  };

  return (
    <div className="download-subscribe-panel">
      <h2 className="govuk-heading-m govuk-!-margin-top-5">
        Subscribe, download the data
      </h2>

      <ul className="govuk-list app-list--nav govuk-!-font-size-19">
        <li>
          {onSubscribeToggle ? (
            <button
              onClick={handleSubscribeToggle}
              disabled={isToggling}
              className="govuk-link download-subscribe-panel__link-button"
              aria-label={subscribed ? 'Unsubscribe from this data set' : 'Subscribe to this data set'}
            >
              {subscribed ? 'Unsubscribe from this data set' : 'Subscribe to this data set'}
            </button>
          ) : (
            <Link
              href={`/data/${datasetId}/subscription`}
              className="govuk-link"
            >
              {subscribed ? 'Unsubscribe from this data set' : 'Subscribe to this data set'}
            </Link>
          )}
        </li>

        <li>
          <a
            href={downloadUrl}
            className="govuk-link"
            download
            aria-label={`Download dataset (.${fileExtension}${fileSize ? `, ${fileSize}` : ''})`}
          >
            Download dataset (.{fileExtension})
            {fileSize && <span className="govuk-!-font-size-16"> ({fileSize})</span>}
          </a>
        </li>
      </ul>

      <style jsx>{`
        .download-subscribe-panel {
          margin-top: 2rem;
        }

        .app-list--nav {
          list-style: none;
          padding: 0;
        }

        .app-list--nav li {
          margin-bottom: 0.75rem;
        }

        .download-subscribe-panel__link-button {
          background: none;
          border: none;
          padding: 0;
          cursor: pointer;
          text-align: left;
          font-size: inherit;
          font-family: inherit;
        }

        .download-subscribe-panel__link-button:hover {
          text-decoration: underline;
          text-decoration-thickness: 3px;
          text-decoration-skip-ink: none;
        }

        .download-subscribe-panel__link-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
}
