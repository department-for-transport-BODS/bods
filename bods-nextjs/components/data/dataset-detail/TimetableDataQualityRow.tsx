/**
 * "Data quality report" row of the timetable property table.
 *
 * Source: transit_odp/browse/templates/browse/timetables/dataset_detail/property_table.html
 *         transit_odp/templates/snippets/data_quality_row.html
 *         transit_odp/browse/templates/browse/snippets/help_modals/data_quality_report.html
 */

import { publishAppPath, publishPath } from '@/config/client';
import { DatasetHelpModal } from './DatasetHelpModal';
import type { DatasetDetailDataQuality } from './types';

interface TimetableDataQualityRowProps {
  dataQuality: DatasetDetailDataQuality;
  organisationId: number;
  datasetId: number;
  isSpecificFeedback: boolean;
}

const TAG_CLASSES = 'govuk-!-margin-left-3 govuk-!-font-size-16 govuk-!-text-align-centre';

/** Django's `warning_data.data.X.count == 0`: a missing level is never zero. */
function hasNoCriticalIssues(dataQuality: DatasetDetailDataQuality, isSpecificFeedback: boolean): boolean {
  if (dataQuality.criticalCount !== 0) return false;
  return isSpecificFeedback ? dataQuality.feedbackCount === 0 : true;
}

export function TimetableDataQualityRow({
  dataQuality,
  organisationId,
  datasetId,
  isSpecificFeedback,
}: TimetableDataQualityRowProps) {
  const reportHref = publishAppPath(
    `/org/${organisationId}/dataset/timetable/${datasetId}/report/${dataQuality.reportId}`,
  );
  const reportLink = (
    <a className="govuk-link" target="_blank" rel="noreferrer" href={reportHref}>
      View data quality report
    </a>
  );

  return (
    <tr className="govuk-table__row">
      <th scope="row" className="govuk-table__header">
        Data quality report
        <DatasetHelpModal heading="Data Quality Report">
          <p className="govuk-body">
            Beyond the usual validation check for the TransXChange 2.4 v1.1 PTI, BODS does additional checks to
            ascertain the quality of the data and assigns a subsequent score to the data set. More information on the
            data quality checks can be{' '}
            <a
              className="govuk-link"
              rel="noopener noreferrer"
              target="_blank"
              href={`${publishPath('/guidance/operator-requirements')}?section=dataquality`}
            >
              found here.
            </a>
          </p>
        </DatasetHelpModal>
      </th>
      <td className="govuk-table__cell">
        {dataQuality.newDqsReport ? (
          <>
            {hasNoCriticalIssues(dataQuality, isSpecificFeedback) ? (
              <span className={`govuk-tag govuk-tag--green ${TAG_CLASSES}`}>NO CRITICAL ISSUES</span>
            ) : (
              <span className={`govuk-tag govuk-tag--red ${TAG_CLASSES}`}>CRITICAL ISSUES</span>
            )}
            <br />
            {reportLink}
          </>
        ) : (
          <div className="stacked">
            Data quality {dataQuality.score}
            <span className={`status-indicator status-indicator--${dataQuality.cssIndicator}`}>
              {dataQuality.ragLevel}
            </span>
          </div>
        )}
      </td>
      <td className="govuk-table__cell">{dataQuality.newDqsReport ? null : reportLink}</td>
    </tr>
  );
}
