/**
 * Main column of the timetable dataset detail page (success content or the
 * "Data set not available" error panel).
 *
 * Source: transit_odp/browse/templates/browse/timetables/dataset_detail/
 *         {success_content,property_table,error_panel,feedback_content}.html
 */

import Link from 'next/link';
import { MapboxRouteMap } from '@/components/data/MapboxRouteMap';
import { datasetListPath, datasetSubpagePath } from '@/lib/dataset-paths';
import { DatasetApiUrlPanel } from './DatasetApiUrlPanel';
import { DatasetFeedbackSection } from './DatasetFeedbackSection';
import { DatasetPropertyTable } from './DatasetPropertyTable';
import { DatasetSubscribeDownload } from './DatasetSubscribeDownload';
import { TimetableDataQualityRow } from './TimetableDataQualityRow';
import { TimetableServiceNumbers } from './TimetableServiceNumbers';
import type { TimetableDatasetDetail } from './types';

interface TimetableDatasetDetailContentProps {
  dataset: TimetableDatasetDetail;
  /** django-waffle `is_specific_feedback` */
  isSpecificFeedback: boolean;
}

function ErrorPanel({ dataset }: { dataset: TimetableDatasetDetail }) {
  const changelogHref = datasetSubpagePath('TIMETABLE', dataset.id, 'changelog');
  const downloadHref = datasetSubpagePath('TIMETABLE', dataset.id, 'download');

  // Django only fills the link for expired / inactive datasets (and the
  // `get_working` variant for errored ones); otherwise the href is empty.
  let previousDataHref = '';
  if (dataset.status === 'expired' || dataset.status === 'inactive') {
    previousDataHref = downloadHref;
  } else if (dataset.status === 'error') {
    previousDataHref = `${downloadHref}?get_working=true`;
  }

  return (
    <>
      <div className="govuk-panel app-panel--error govuk-!-padding-top-9 govuk-!-padding-bottom-9 govuk-!-margin-bottom-0">
        <h2 className="govuk-heading-xl govuk-panel__title govuk-!-font-size-36">Data set not available</h2>
      </div>
      <table className="govuk-table dataset-property-table">
        <tbody className="govuk-table__body">
          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Name
            </th>
            <td className="govuk-table__cell dont-break-out">{dataset.name}</td>
          </tr>
          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Owner
            </th>
            <td className="govuk-table__cell">{dataset.organisationName}</td>
          </tr>
          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Last updated
            </th>
            <td className="govuk-table__cell">
              <div className="flex-between">
                <span>
                  {dataset.lastUpdated} by {dataset.publishedBy ?? 'System'}
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
        There is currently an error in this data set. The operator has been informed. Whilst the issue is being
        fixed you can use the pre-exisiting data set below.
      </p>
      <table className="govuk-table">
        <tbody>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell govuk-summary-list__row--no-border">TransXChange version</td>
            <td className="govuk-table__cell govuk-summary-list__row--no-border">
              <div className="flex-between">
                <span>{dataset.transxchangeVersion}</span>
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
        <h3 className="govuk-heading-m govuk-!-font-size-27">Would you like to provide feedback on this data set?</h3>
        <Link
          role="button"
          className="govuk-button govuk-button--secondary"
          href={datasetSubpagePath('TIMETABLE', dataset.id, 'feedback')}
        >
          Provide feedback
        </Link>
      </div>
    </>
  );
}

function SuccessContent({ dataset, isSpecificFeedback }: TimetableDatasetDetailContentProps) {
  return (
    <>
      <MapboxRouteMap revisionId={dataset.revisionId} />
      <DatasetPropertyTable
        id={dataset.id}
        name={dataset.name}
        dataTypeLabel="Timetables data"
        datasetType="TIMETABLE"
        description={dataset.description}
        organisationName={dataset.organisationName}
        ownerHref={datasetListPath('TIMETABLE', { organisation: dataset.organisationId, status: 'live' })}
        status={dataset.status}
      >
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            TransXChange version
          </th>
          <td className="govuk-table__cell" colSpan={2}>
            {dataset.transxchangeVersion}
          </td>
        </tr>
        {dataset.dataQuality ? (
          <TimetableDataQualityRow
            dataQuality={dataset.dataQuality}
            organisationId={dataset.organisationId}
            datasetId={dataset.id}
            isSpecificFeedback={isSpecificFeedback}
          />
        ) : null}
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Last updated
          </th>
          <td className="govuk-table__cell dont-break-out">{dataset.lastUpdated}</td>
          <td className="govuk-table__cell">
            <Link className="govuk-link" href={datasetSubpagePath('TIMETABLE', dataset.id, 'changelog')}>
              View change log
            </Link>
          </td>
        </tr>
      </DatasetPropertyTable>
      <TimetableServiceNumbers datasetId={dataset.id} licences={dataset.serviceNumbers} />
      {dataset.feedApi ? <DatasetApiUrlPanel apiUrl={dataset.feedApi} datasetType="TIMETABLE" /> : null}
      <DatasetSubscribeDownload
        datasetId={dataset.id}
        datasetType="TIMETABLE"
        isSubscribed={dataset.isSubscribed}
        fileExtension={dataset.uploadFileExtension}
      />
      {isSpecificFeedback ? null : <DatasetFeedbackSection datasetId={dataset.id} datasetType="TIMETABLE" />}
    </>
  );
}

export function TimetableDatasetDetailContent(props: TimetableDatasetDetailContentProps) {
  return props.dataset.error ? <ErrorPanel dataset={props.dataset} /> : <SuccessContent {...props} />;
}
