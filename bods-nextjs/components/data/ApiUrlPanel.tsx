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

'use client';

import { useState } from 'react';
import styles from './ApiUrlPanel.module.css';

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
    <div className={styles.wrapper}>
      <h2 className="govuk-heading-m">{panelTitle}</h2>

      <div className={styles.panel}>
        <span
          id="code-snippet-url"
          className={styles.url}
          role="textbox"
          aria-label="API endpoint URL"
          aria-readonly="true"
        >
          {apiUrl}
        </span>

        <button
          className={`govuk-button govuk-button--secondary ${styles.copyButton}`}
          onClick={handleCopy}
          aria-label="Copy API endpoint URL to clipboard"
          type="button"
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
    </div>
  );
}
