'use client';

/**
 * API URL Panel Component
 *
 * Source: transit_odp/browse/templates/browse/base/api_url_panel.html
 *
 * Displays API endpoint URL for programmatic access:
 * - Feed endpoint URL
 * - Copy to clipboard functionality
 * - Works for both AVL feeds and API access
 *
 */

import { useState } from 'react';

export interface ApiUrlPanelProps {
  /** API endpoint URL */
  apiUrl: string;
  /** Title override (default based on context) */
  title?: string;
  /** Dataset type to determine title */
  datasetType?: 'TIMETABLE' | 'AVL' | 'FARES';
}

export function ApiUrlPanel({
  apiUrl,
  title,
  datasetType = 'TIMETABLE',
}: ApiUrlPanelProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(apiUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const panelTitle = title || (
    datasetType === 'AVL'
      ? 'Use this data feed in your code'
      : 'Use this data set in your code'
  );

  return (
    <div className="api-url-panel-wrapper">
      <h2 className="govuk-heading-m">{panelTitle}</h2>

      <div className="api-url-panel">
        <span
          id="code-snippet-url"
          className="api-url-panel__url dont-break-out"
          role="textbox"
          aria-label="API endpoint URL"
          aria-readonly="true"
        >
          {apiUrl}
        </span>

        <button
          className="govuk-button govuk-button--secondary api-url-panel__copy-button"
          onClick={handleCopy}
          aria-label="Copy API endpoint URL to clipboard"
          type="button"
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>

      <style jsx>{`
        .api-url-panel-wrapper {
          margin-top: 2rem;
          margin-bottom: 2rem;
        }

        .api-url-panel {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 1rem;
          background-color: #f3f2f1;
          border: 1px solid #b1b4b6;
          border-radius: 0;
          word-break: break-all;
        }

        .api-url-panel__url {
          flex: 1;
          font-family: monospace;
          font-size: 0.875rem;
          line-height: 1.4;
          color: #0b0c0c;
        }

        .api-url-panel__copy-button {
          flex-shrink: 0;
          margin: 0;
          white-space: nowrap;
        }

        .dont-break-out {
          overflow-wrap: break-word;
          word-wrap: break-word;
          word-break: break-word;
          hyphens: auto;
        }

        @media (max-width: 640px) {
          .api-url-panel {
            flex-direction: column;
            align-items: stretch;
          }

          .api-url-panel__copy-button {
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
}
