import Link from 'next/link';
import { dataPath, publishAppPath } from '@/config/client';
import type { TimetableFeedDataQuality, TimetableFeedDetail } from './timetableFeedDetailTypes';
import { timetableFeedStatusIndicator } from './timetableFeedStatus';

interface TimetableFeedDetailTableProps {
  feed: TimetableFeedDetail;
}

function DataQualityScore({ dataQuality }: { dataQuality: TimetableFeedDataQuality }) {
  if (dataQuality.isNewService) {
    return dataQuality.hasCriticalIssues ? (
      <span className="govuk-tag govuk-tag--red govuk-!-margin-left-3 govuk-!-font-size-16 govuk-!-text-align-centre">
        CRITICAL ISSUES
      </span>
    ) : (
      <span className="govuk-tag govuk-tag--green govuk-!-margin-left-3 govuk-!-font-size-16 govuk-!-text-align-centre">
        NO CRITICAL ISSUES
      </span>
    );
  }

  if (!dataQuality.rag) return null;

  return (
    <>
      {dataQuality.rag.score}{' '}
      <span className={`status-indicator status-indicator--${dataQuality.rag.cssIndicator} govuk-!-font-weight-bold`}>
        {dataQuality.rag.ragLevel.toUpperCase()}
      </span>
    </>
  );
}

export function TimetableFeedDetailTable({ feed }: TimetableFeedDetailTableProps) {
  const datasetPath = `/org/${feed.orgId}/dataset/timetable/${feed.datasetId}`;
  const editHref = publishAppPath(`${datasetPath}/dataset-edit`);
  const downloadHref = publishAppPath(`${datasetPath}/download`);
  const status = timetableFeedStatusIndicator(feed.datasetStatus);
  const { dataQuality } = feed;
  const hasQualityScore = dataQuality.isNewService || dataQuality.rag !== null;
  const reportPath = dataQuality.reportId ? `${datasetPath}/report/${dataQuality.reportId}` : null;

  return (
    <table className="govuk-table dataset-property-table">
      <tbody className="govuk-table__body">
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header govuk-!-width-one-quarter">
            Name
          </th>
          <td className="govuk-table__cell dont-break-out">{feed.name}</td>
        </tr>

        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Data set ID
          </th>
          <td className="govuk-table__cell dont-break-out">{feed.datasetId}</td>
        </tr>

        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            URL link
          </th>
          <td className="govuk-table__cell">
            <span className="no-wrap right-justify" id="id-publish-review-url-link">
              <a className="govuk-link" href={feed.urlLink ?? `${downloadHref}?is_review=false`}>
                Publisher URL
              </a>
            </span>
          </td>
        </tr>

        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Description
          </th>
          <td className="govuk-table__cell">
            <div className="flex-between">
              {feed.description}
              <span>
                <Link className="govuk-link right-justify" href={editHref}>
                  Edit
                </Link>
              </span>
            </div>
          </td>
        </tr>

        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Short description
          </th>
          <td className="govuk-table__cell">
            <div className="flex-between">
              {feed.shortDescription}
              <Link className="govuk-link" href={editHref}>
                Edit
              </Link>
            </div>
          </td>
        </tr>

        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Status
          </th>
          <td className="govuk-table__cell">
            <div className="flex-between">
              <span className={`status-indicator ${status.className}`.trim()}>{status.label}</span>
              <a className="govuk-link" href={dataPath(`/timetable/dataset/${feed.datasetId}`)}>
                Preview developer view
              </a>
            </div>
          </td>
        </tr>

        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Data quality report
          </th>
          <td className="govuk-table__cell">
            {hasQualityScore ? (
              <p className="govuk-!-margin-top-0 govuk-!-margin-bottom-1">
                <DataQualityScore dataQuality={dataQuality} />
              </p>
            ) : null}
            <span className="no-wrap right-justify" id="id-publish-review-quality-report">
              {reportPath ? (
                <>
                  <a
                    className="govuk-link"
                    target="_blank"
                    rel="noopener noreferrer"
                    href={publishAppPath(reportPath)}
                  >
                    View data quality report
                  </a>
                  <br />
                  <a className="govuk-link" target="_blank" href={publishAppPath(`${reportPath}/csv`)}>
                    Download data quality report.csv
                  </a>
                </>
              ) : (
                'Generating...'
              )}
            </span>
          </td>
        </tr>

        {feed.showPti ? (
          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              TransXChange Validation Report
            </th>
            <td className="govuk-table__cell">
              {feed.hasPtiViolations ? (
                <>
                  <p className="govuk-body govuk-!-font-weight-bold">3a Validation check – Passed with issues</p>
                  <p className="govuk-body">
                    <a className="govuk-link" href={publishAppPath(`${datasetPath}/violations-csv`)}>
                      Download validation report
                    </a>
                  </p>
                  <p className="govuk-body">
                    Some of the files in the data supplied is non-compliant. It does not meet the data format
                    required. To pass the validation please address all outstanding issues in the validation report
                    and update the data set.
                  </p>
                </>
              ) : (
                <>
                  <p className="govuk-body govuk-!-font-weight-bold">Successfully passed validation</p>
                  <p className="govuk-body">Your data is BODS compliant.</p>
                </>
              )}
            </td>
          </tr>
        ) : null}

        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Owner
          </th>
          <td className="govuk-table__cell">{feed.ownerName}</td>
        </tr>

        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            TransXChange version
          </th>
          <td className="govuk-table__cell">{feed.transxchangeVersion}</td>
        </tr>

        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Download TransXChange
          </th>
          <td className="govuk-table__cell">
            <a className="govuk-link" href={feed.urlLink ?? downloadHref}>
              Download .xml (TxC)
            </a>
          </td>
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
  );
}
