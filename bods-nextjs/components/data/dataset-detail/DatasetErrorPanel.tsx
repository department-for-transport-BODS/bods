/**
 * "Data set not available" error panel shown instead of the success content
 * when a dataset's live revision is in error.
 *
 * Source: transit_odp/browse/templates/browse/timetables/dataset_detail/error_panel.html
 *         transit_odp/browse/templates/browse/fares/feed_detail/error_panel.html
 *         (identical but for the heading and the sub-page links)
 */

import Link from 'next/link';

interface DatasetErrorPanelProps {
  /** "Data set not available" (timetables) or "Data feed not available" (fares) */
  heading: string;
  name: string;
  organisationName: string;
  lastUpdated: string | null;
  publishedBy: string | null;
  transxchangeVersion: string;
  changelogHref: string;
  /** Django leaves this empty unless the data set is expired, inactive or in error */
  previousDataHref: string;
  feedbackHref: string;
}

export function DatasetErrorPanel({
  heading,
  name,
  organisationName,
  lastUpdated,
  publishedBy,
  transxchangeVersion,
  changelogHref,
  previousDataHref,
  feedbackHref,
}: DatasetErrorPanelProps) {
  return (
    <>
      <div className="govuk-panel app-panel--error govuk-!-padding-top-9 govuk-!-padding-bottom-9 govuk-!-margin-bottom-0">
        <h2 className="govuk-heading-xl govuk-panel__title govuk-!-font-size-36">{heading}</h2>
      </div>
      <table className="govuk-table dataset-property-table">
        <tbody className="govuk-table__body">
          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Name
            </th>
            <td className="govuk-table__cell dont-break-out">{name}</td>
          </tr>
          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Owner
            </th>
            <td className="govuk-table__cell">{organisationName}</td>
          </tr>
          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Last updated
            </th>
            <td className="govuk-table__cell">
              <div className="flex-between">
                <span>
                  {lastUpdated} by {publishedBy ?? 'System'}
                </span>
                <span className="right-justify">
                  <Link className="govuk-link" href={changelogHref}>
                    View change log
                  </Link>
                </span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <h2 className="govuk-heading-m govuk-!-font-size-27">Download previous data</h2>
      <p className="govuk-body-m">
        There is currently an error in this data set. The operator has been informed. Whilst the issue is
        being fixed you can use the pre-exisiting data set below.
      </p>
      <table className="govuk-table">
        <tbody>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell govuk-summary-list__row--no-border">TransXChange version</td>
            <td className="govuk-table__cell govuk-summary-list__row--no-border">
              <div className="flex-between">
                <span>{transxchangeVersion}</span>
                <span className="right-justify no-wrap">
                  <a className="govuk-link" href={previousDataHref}>
                    Download .xml (TransXChange format)
                  </a>
                </span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div id="user-feed-back-section">
        <h3 className="govuk-heading-m govuk-!-font-size-27">
          Would you like to provide feedback on this data set?
        </h3>
        <Link role="button" className="govuk-button govuk-button--secondary" href={feedbackHref}>
          Provide feedback
        </Link>
      </div>
    </>
  );
}
