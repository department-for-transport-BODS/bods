import Link from 'next/link';
import { publishAppPath } from '@/config/client';
import type { TimetableFeedDetail } from './timetableFeedDetailTypes';

/**
 * Source: transit_odp/publish/templates/publish/dataset_detail/error_panel.html
 */
export function TimetableFeedDetailErrorPanel({ feed }: { feed: TimetableFeedDetail }) {
  const datasetPath = `/org/${feed.orgId}/dataset/timetable/${feed.datasetId}`;

  return (
    <>
      <div className="govuk-panel app-panel--error govuk-!-padding-top-9 govuk-!-padding-bottom-9 govuk-!-margin-bottom-7">
        <h2 className="govuk-heading-xl govuk-panel__title govuk-!-font-size-36">Data set not available</h2>
      </div>
      <div
        className="govuk-error-summary govuk-!-margin-bottom-0"
        aria-labelledby="error-summary-title"
        role="alert"
        tabIndex={-1}
        data-module="govuk-error-summary"
      >
        <h2 className="govuk-error-summary__title govuk-!-margin-bottom-2" id="error-summary-title">
          There is a problem
        </h2>
        <div className="govuk-error-summary__body">
          <ul className="govuk-list govuk-error-summary__list govuk-!-margin-bottom-6">
            {feed.severeErrors.map((description, index) => (
              <li key={`${index}-${description}`} className="app-error-summary__item">
                {description}
              </li>
            ))}
          </ul>
          <Link
            role="button"
            className="govuk-button govuk-!-margin-bottom-0"
            href={publishAppPath(`${datasetPath}/update`)}
          >
            Publish correct data set
          </Link>
        </div>
      </div>
      <table className="govuk-table dataset-property-table">
        <tbody className="govuk-table__body">
          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Name
            </th>
            <td className="govuk-table__cell dont-break-out">{feed.name}</td>
          </tr>
          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Owner
            </th>
            <td className="govuk-table__cell">{feed.ownerName}</td>
          </tr>
          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Last updated
            </th>
            <td className="govuk-table__cell">
              <div className="flex-between">
                <span>
                  {feed.publishedAtDisplay} by {feed.publishedBy ?? 'System'}
                </span>
                <span className="right-justify">
                  <a className="govuk-link" href={publishAppPath(`${datasetPath}/changelog`)}>
                    View change log
                  </a>
                </span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <h3 className="govuk-heading-m">What should I do next?</h3>
      <p className="govuk-body govuk-!-font-size-16">
        You can re-upload a different data feed file again. Please ensure that your provided data format is correct
        and that your feed file contains valid data.
      </p>
      <p className="govuk-body govuk-!-font-size-16">
        You can delete this data set to stop using https://www.arriva.co.uk/timetables
      </p>
      <p className="govuk-body app-!-text-muted govuk-!-font-size-16">Accepted file formats include .xml (TransXChange).</p>
      <Link role="button" className="govuk-button govuk-button--secondary" href={publishAppPath(`${datasetPath}/delete`)}>
        Delete data
      </Link>
    </>
  );
}
