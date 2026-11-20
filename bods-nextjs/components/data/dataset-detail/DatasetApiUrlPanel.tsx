'use client';

/**
 * Source: transit_odp/browse/templates/browse/base/api_url_panel.html
 *
 * Rendered by the caller only when a feed API URL exists (signed-in users).
 */

interface DatasetApiUrlPanelProps {
  apiUrl: string;
  /** AVL says "data feed" where the others say "data set" */
  datasetType?: 'TIMETABLE' | 'AVL' | 'FARES';
}

export function DatasetApiUrlPanel({ apiUrl, datasetType = 'TIMETABLE' }: DatasetApiUrlPanelProps) {
  return (
    <>
      <h2 className="govuk-heading-m">
        {datasetType === 'AVL' ? 'Use this data feed in your code' : 'Use this data set in your code'}
      </h2>
      <div className="api-url-panel">
        <span id="code-snippet-url" className="api-url-panel__url dont-break-out">
          {apiUrl}
        </span>
        <button
          type="button"
          className="govuk-button govuk-button--link"
          aria-label="Copy Code snippet to clipboard"
          onClick={() => {
            navigator.clipboard?.writeText(apiUrl).catch(() => undefined);
          }}
        >
          Copy
        </button>
      </div>
    </>
  );
}
