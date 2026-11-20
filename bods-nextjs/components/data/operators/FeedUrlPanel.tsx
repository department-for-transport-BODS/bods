'use client';

import { useState } from 'react';

interface FeedUrlPanelProps {
  /** Label above the panel, e.g. "Timetables data API feed URL". */
  label: string;
  /** Django's element id, e.g. `timetable-feed-url`. */
  id: string;
  url: string;
}

/**
 * Django's operator-page feed URL block: a bordered `.api-url-panel` with the
 * URL and a link-style Copy button (`BODSFrontend.copyToClipboard`).
 */
export function FeedUrlPanel({ label, id, url }: FeedUrlPanelProps) {
  const [copyFailed, setCopyFailed] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(url);
      setCopyFailed(false);
    } catch {
      setCopyFailed(true);
    }
  };

  return (
    <>
      <p className="govuk-body-m govuk-!-padding-top-3">{label}</p>
      <div className="govuk-grid-row govuk-!-margin-0 api-url-panel">
        <div className="govuk-grid-column-three-quarters govuk-!-padding-0">
          <p className="api-url-panel__url govuk-!-margin-3 dont-break-out" id={id}>
            {url}
          </p>
        </div>
        <div className="govuk-grid-column-one-quarter govuk-!-padding-2">
          <button
            type="button"
            className="govuk-button govuk-button--link govuk-!-margin-left-9"
            aria-label="Copy code snippet to clipboard"
            onClick={copy}
          >
            Copy
          </button>
          {copyFailed && <span className="govuk-visually-hidden">Unable to copy</span>}
        </div>
      </div>
    </>
  );
}
